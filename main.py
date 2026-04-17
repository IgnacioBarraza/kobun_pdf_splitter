from pathlib import Path

from kobun.application.use_cases.split_pdf_use_case import SplitPdfUseCase
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService
from kobun.infrastructure.pdf_engine.pdf_engine_adapter import PdfEngineAdapter
from kobun.infrastructure.repositories.pdf_repository_impl import PyMuPdfRepository


def run_test_cli(use_case: SplitPdfUseCase):
    """
    Función de prueba para validar la arquitectura sin UI.
    """
    print("\n--- 🌸 Kobun PDF Manager: Architecture Test ---")

    # Simulación de entrada de usuario
    input_file = input("Introduce la ruta del PDF de origen: ").strip()
    start_p = int(input("Página de inicio: "))
    end_p = int(input("Página de fin: "))

    input_path = Path(input_file)
    output_path = input_path.parent / f"kobun_split_{start_p}_{end_p}.pdf"

    try:
        print(f"\n[1/3] Procesando: {input_path.name}...")
        result_doc = use_case.execute(
            input_path=input_path,
            output_path=output_path,
            start=start_p,
            end=end_p
        )

        print(f"[2/3] Éxito: Documento '{result_doc.metadata.title}' procesado.")
        print(f"[3/3] Guardado en: {output_path}")

    except Exception as e:
        print(f"\n[ERROR DE ARQUITECTURA]: {str(e)}")


def main():
    engine = PdfEngineAdapter()
    pdf_repository = PyMuPdfRepository(engine)
    pdf_service = PdfSplitterService()

    split_use_case = SplitPdfUseCase(pdf_repository, pdf_service)

    run_test_cli(split_use_case)


if __name__ == "__main__":
    main()