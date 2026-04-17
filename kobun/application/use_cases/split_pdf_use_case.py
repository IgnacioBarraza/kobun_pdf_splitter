from pathlib import Path

from kobun.application.interfaces.pdf_repository import PdfRepository
from kobun.domain.pdf.entities.pdf_document import PdfDocument, PdfProcessingStatus
from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService
from kobun.domain.pdf.value_objects.page_range import PageRange


class SplitPdfUseCase:
    def __init__(self, pdf_repository: PdfRepository, pdf_service: PdfSplitterService):
        self._pdf_repository = pdf_repository
        self._pdf_service = pdf_service

    def execute(self, input_path: Path, output_path: Path, start: int, end: int) -> PdfDocument:
        page_range = PageRange(start=start, end=end)
        document = self._pdf_repository.open_document(input_path)

        self._pdf_service.validate_ranges(document, [page_range])
        document.mark_as_processing()

        try:
            result = self._pdf_repository.split_page_range(
                src_doc=document,
                output_doc=output_path,
                page_range=page_range
            )

            document.mark_as_processed(page_count=document.page_count)
            return result

        except Exception as e:
            document.mark_as_failed()
            raise e

    def _validate_business_rules(self, doc: PdfDocument, p_range: PageRange) -> None:
        """
        Valida que la operación sea lícita según el estado y contenido del PDF.
        """
        if doc.page_count is None:
            raise InvalidPdfException("No se pudo determinar el número de páginas del PDF original.")

        if p_range.end > doc.page_count:
            raise InvalidPdfException(
                f"Rango inválido. El PDF tiene {doc.page_count} páginas, "
                f"pero se solicitó hasta la {p_range.end}."
            )

        if doc.status != PdfProcessingStatus.UPLOADED:
            raise InvalidPdfException("El documento ya ha sido procesado o está en un estado inválido.")