from pathlib import Path

from kobun.application.interfaces.pdf_repository import PdfRepository
from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService


class LoadPdfUseCase:
    """
    Opens a PDF and guarantees it is usable, so the UI can show its name,
    page count and metadata before asking for a range.

    It is the single entry point for loading a file: both the "pick a file"
    button and drag & drop have to come through here, because this is where
    files that are not readable PDFs get rejected.
    """

    def __init__(self, pdf_repository: PdfRepository, pdf_service: PdfSplitterService):
        self._pdf_repository = pdf_repository
        self._pdf_service = pdf_service

    def execute(self, file_path: Path) -> PdfDocument:
        """
        :param file_path: Path of the PDF to load.
        :return: The validated document, ready to be split.
        :raises PdfNotFoundException: If the path does not exist.
        :raises EncryptedPdfException: If the PDF asks for a password.
        :raises InvalidPdfException: If it is not a readable PDF or has no pages.
        """
        document = self._pdf_repository.open_document(Path(file_path))
        self._pdf_service.validate_document_for_processing(document)

        return document
