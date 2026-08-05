from pathlib import Path

from kobun.application.interfaces.pdf_repository import PdfRepository
from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService
from kobun.domain.pdf.value_objects.page_selection import PageSelection


class SplitPdfUseCase:
    """
    Orquesta la extracción de una selección de páginas hacia un PDF nuevo.
    """

    def __init__(self, pdf_repository: PdfRepository, pdf_service: PdfSplitterService):
        self._pdf_repository = pdf_repository
        self._pdf_service = pdf_service

    def execute(self, input_path: Path, output_path: Path, selection: PageSelection) -> PdfDocument:
        """
        :param input_path: PDF de origen.
        :param output_path: Ruta del PDF a generar.
        :param selection: Páginas a extraer, 1-based (ej. "1-5,10-15").
        :return: El PdfDocument resultante.
        """
        document = self._pdf_repository.open_document(input_path)

        self._pdf_service.validate_selection(document, selection)
        document.mark_as_processing()

        try:
            metadata = self._pdf_service.prepare_split_metadata(document, selection)
            result = self._pdf_repository.split_page_selection(
                src_doc=document,
                output_doc=output_path,
                selection=selection,
                metadata=metadata,
            )

            document.mark_as_processed()
            return result

        except Exception:
            document.mark_as_failed()
            raise
