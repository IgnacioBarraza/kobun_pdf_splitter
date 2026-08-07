from pathlib import Path

from kobun.application.dto.split_pdf_request import SplitPdfRequest
from kobun.application.services.output_path_resolver import OutputPathResolver
from kobun.application.use_cases.list_history_use_case import ListHistoryUseCase
from kobun.application.use_cases.load_pdf_use_case import LoadPdfUseCase
from kobun.application.use_cases.record_split_use_case import RecordSplitUseCase
from kobun.application.use_cases.split_pdf_use_case import SplitPdfUseCase
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService
from kobun.domain.pdf.value_objects.overwrite_policy import OverwritePolicy
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.infrastructure.config.infrastructure_settings import AppDirectories
from kobun.infrastructure.filesystem.local_file_storage import LocalFileStorage
from kobun.infrastructure.pdf_engine.pdf_engine_adapter import PdfEngineAdapter
from kobun.infrastructure.repositories.json_history_repository import JsonHistoryRepository
from kobun.infrastructure.repositories.pdf_repository_impl import PyMuPdfRepository
from kobun.shared.config.app_settings import HISTORY_FILENAME


def print_history(list_history_use_case: ListHistoryUseCase, limit: int = 5) -> None:
    entries = list_history_use_case.execute(limit=limit)

    if not entries:
        return

    print(f"\n--- Últimas {len(entries)} exportaciones ---")
    for entry in entries:
        marca = " " if entry.is_available else "✗"
        cuando = entry.record.created_at.astimezone().strftime("%d/%m %H:%M")
        print(f"{marca} {cuando}  {entry.record}")


def run_test_cli(
    load_use_case: LoadPdfUseCase,
    split_use_case: SplitPdfUseCase,
    record_use_case: RecordSplitUseCase,
    list_history_use_case: ListHistoryUseCase,
) -> None:
    """
    CLI provisional para ejercitar el dominio sin UI.
    Se reemplazará cuando la ventana de Qt esté conectada.
    """
    print("\n--- 🌸 Kobun PDF Manager: Architecture Test ---")
    print_history(list_history_use_case)

    try:
        document = load_use_case.execute(Path(input("\nRuta del PDF de origen: ").strip()))
        print(f"\nCargado: {document.filename} — {document.page_count} páginas")
        print(f"Título: {document.metadata.title} | Autor: {document.metadata.author}")

        selection = PageSelection.parse(input("\nPáginas a extraer (ej. 1-5,10-15 o 7): ").strip())
        print(f"Se extraerán {selection.total_pages} páginas: {selection}")

        suggested = split_use_case.suggest_output_path(document, selection)
        print(f"\nDestino sugerido: {suggested}")
        raw_output = input("Destino (Enter para el sugerido, o archivo .pdf / carpeta): ").strip()

        print("\nProcesando...")
        response = split_use_case.execute(SplitPdfRequest(
            input_path=document.storage_path,
            selection=selection,
            output_path=Path(raw_output) if raw_output else None,
            policy=OverwritePolicy.RENAME,
        ))

        print(f"Listo: '{response.title}' con {response.page_count} páginas")
        print(f"Guardado en: {response.output_path}")

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        return

    # El registro va fuera del try del split: si el historial falla, el PDF ya
    # está en disco y el usuario no debe ver el trabajo como fallido.
    try:
        record_use_case.execute(response)
    except Exception as e:
        print(f"[AVISO] No se pudo registrar en el historial: {type(e).__name__}: {e}")

    print_history(list_history_use_case)


def main() -> None:
    directories = AppDirectories()
    file_storage = LocalFileStorage()

    pdf_repository = PyMuPdfRepository(PdfEngineAdapter())
    pdf_service = PdfSplitterService()
    history_repository = JsonHistoryRepository(directories.data_file(HISTORY_FILENAME))

    load_use_case = LoadPdfUseCase(pdf_repository, pdf_service)
    split_use_case = SplitPdfUseCase(
        pdf_repository, pdf_service, OutputPathResolver(file_storage)
    )
    record_use_case = RecordSplitUseCase(history_repository)
    list_history_use_case = ListHistoryUseCase(history_repository, file_storage)

    run_test_cli(load_use_case, split_use_case, record_use_case, list_history_use_case)


if __name__ == "__main__":
    main()
