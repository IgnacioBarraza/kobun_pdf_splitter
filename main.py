from pathlib import Path

from kobun.application.use_cases.split_pdf_use_case import SplitPdfUseCase
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.infrastructure.pdf_engine.pdf_engine_adapter import PdfEngineAdapter
from kobun.infrastructure.repositories.pdf_repository_impl import PyMuPdfRepository


def run_test_cli(use_case: SplitPdfUseCase) -> None:
    """
    CLI provisional para ejercitar el dominio sin UI.
    Se reemplazará cuando la ventana de Qt esté conectada.
    """
    print("\n--- 🌸 Kobun PDF Manager: Architecture Test ---")

    input_file = input("Introduce la ruta del PDF de origen: ").strip()
    raw_selection = input("Páginas a extraer (ej. 1-5,10-15 o 7): ").strip()

    input_path = Path(input_file)

    try:
        selection = PageSelection.parse(raw_selection)
        output_path = input_path.parent / f"kobun_split_{str(selection).replace(',', '_')}.pdf"

        print(f"\n[1/3] Procesando {input_path.name}: páginas {selection} ({selection.total_pages} en total)...")
        result_doc = use_case.execute(
            input_path=input_path,
            output_path=output_path,
            selection=selection,
        )

        print(f"[2/3] Éxito: Documento '{result_doc.metadata.title}' generado con {result_doc.page_count} páginas.")
        print(f"[3/3] Guardado en: {output_path}")

    except Exception as e:
        print(f"\n[ERROR]: {type(e).__name__}: {e}")


def main() -> None:
    engine = PdfEngineAdapter()
    pdf_repository = PyMuPdfRepository(engine)
    pdf_service = PdfSplitterService()

    split_use_case = SplitPdfUseCase(pdf_repository, pdf_service)

    run_test_cli(split_use_case)


if __name__ == "__main__":
    main()
