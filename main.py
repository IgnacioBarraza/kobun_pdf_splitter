from pathlib import Path

from kobun.application.dto.split_pdf_request import SplitPdfRequest
from kobun.application.services.output_path_resolver import OutputPathResolver
from kobun.application.use_cases.load_pdf_use_case import LoadPdfUseCase
from kobun.application.use_cases.split_pdf_use_case import SplitPdfUseCase
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService
from kobun.domain.pdf.value_objects.overwrite_policy import OverwritePolicy
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.infrastructure.filesystem.local_file_storage import LocalFileStorage
from kobun.infrastructure.pdf_engine.pdf_engine_adapter import PdfEngineAdapter
from kobun.infrastructure.repositories.pdf_repository_impl import PyMuPdfRepository


def run_test_cli(load_use_case: LoadPdfUseCase, split_use_case: SplitPdfUseCase) -> None:
    """
    CLI provisional para ejercitar el dominio sin UI.
    Se reemplazará cuando la ventana de Qt esté conectada.
    """
    print("\n--- 🌸 Kobun PDF Manager: Architecture Test ---")

    try:
        document = load_use_case.execute(Path(input("Ruta del PDF de origen: ").strip()))
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
        print(f"Resumen: {response}")

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")


def main() -> None:
    engine = PdfEngineAdapter()
    pdf_repository = PyMuPdfRepository(engine)
    pdf_service = PdfSplitterService()
    output_path_resolver = OutputPathResolver(LocalFileStorage())

    load_use_case = LoadPdfUseCase(pdf_repository, pdf_service)
    split_use_case = SplitPdfUseCase(pdf_repository, pdf_service, output_path_resolver)

    run_test_cli(load_use_case, split_use_case)


if __name__ == "__main__":
    main()
