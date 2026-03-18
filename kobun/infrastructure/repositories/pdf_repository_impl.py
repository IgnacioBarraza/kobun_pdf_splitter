from pathlib import Path
from typing import List
import hashlib

from kobun.application.interfaces.pdf_repository import PdfRepository
from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.value_objects.page_range import PageRange
from kobun.domain.pdf.value_objects.pdf_metadata import PdfMetadata
from kobun.infrastructure.pdf_engine.pdf_engine_adapter import PdfEngineAdapter


class PyMuPdfRepository(PdfRepository):
    """
    Concrete implementation of PdfRepository using PyMuPDF via PdfEngineAdapter.

    This class acts as a bridge between the domain layer (PdfDocument)
    and the underlying PDF engine.
    """

    def __init__(self, engine: PdfEngineAdapter):
        self.engine = engine

    # =========================
    # Internal Helpers
    # =========================

    def _calculate_checksum(self, file_path: Path) -> str:
        """
        Calculates SHA256 checksum of a file.

        :param file_path: Path to the file.
        :return: Hexadecimal checksum string.
        """
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    def _build_pdf_document(self, file_path: Path) -> PdfDocument:
        """
        Builds a PdfDocument entity from a file path.

        :param file_path: Path to the PDF file.
        :return: PdfDocument instance.
        """
        doc = self.engine.open_document(file_path)

        metadata = doc.metadata
        page_count = self.engine.get_page_count(doc)

        self.engine.close_document(doc)

        pdf_document = PdfDocument(
            filename=file_path.name,
            storage_path=file_path,
            size_bytes=file_path.stat().st_size,
            checksum=self._calculate_checksum(file_path),
            metadata=metadata
        )

        pdf_document.page_count = page_count

        return pdf_document

    # =========================
    # Public API
    # =========================

    def open_document(self, file_path: Path) -> PdfDocument:
        """
        Opens a PDF and maps it to a domain entity.

        :param file_path: Path to the PDF file.
        :return: PdfDocument entity.
        """
        return self._build_pdf_document(file_path)

    def close_document(self, document: PdfDocument) -> None:
        """
        No-op for domain entity.

        Engine-level closing is handled internally.
        """
        pass

    def get_page_count(self, document: PdfDocument) -> int:
        """
        Returns the number of pages from the domain entity.

        :param document: PdfDocument instance.
        :return: Page count.
        """
        if document.page_count is None:
            raise ValueError("Page count is not initialized.")
        return document.page_count

    def create_empty_document(self) -> PdfDocument:
        """
        Creates an empty PDF and returns it as a domain entity.

        :return: PdfDocument instance.
        """
        temp_path = Path("empty.pdf")

        doc = self.engine.create_empty_document()
        self.engine.save_document(doc, temp_path)
        self.engine.close_document(doc)

        return self._build_pdf_document(temp_path)

    def extract_metadata(self, document: PdfDocument):
        """
        Returns metadata from the domain entity.

        :param document: PdfDocument instance.
        :return: PdfMetadata
        """
        return document.metadata

    def extract_text(self, document: PdfDocument, page_number: int) -> str:
        """
        Extracts text from a specific page.

        :param document: PdfDocument instance.
        :param page_number: 1-based page index.
        :return: Extracted text.
        """
        doc = self.engine.open_document(document.storage_path)

        try:
            text = self.engine.extract_text(doc, page_number - 1)
        finally:
            self.engine.close_document(doc)

        return text

    def split_single_page(
        self,
        src_doc: PdfDocument,
        output_doc: Path,
        page_index: int
    ) -> PdfDocument:
        """
        Splits a single page into a new PDF.

        :param src_doc: Source PdfDocument.
        :param output_doc: Output file path.
        :param page_index: 1-based page index.
        :return: New PdfDocument.
        """
        source = self.engine.open_document(src_doc.storage_path)

        try:
            new_doc = self.engine.split_single_page(source, page_index)
            self.engine.save_document(new_doc, output_doc)
        finally:
            self.engine.close_document(source)
            self.engine.close_document(new_doc)

        return self._build_pdf_document(output_doc)

    def split_page_range(
        self,
        src_doc: PdfDocument,
        output_doc: Path,
        page_range: PageRange
    ) -> PdfDocument:
        """
        Splits a range of pages into a new PDF.

        :param src_doc: Source PdfDocument.
        :param output_doc: Output file path.
        :param page_range: PageRange value object.
        :return: New PdfDocument.
        """
        source = self.engine.open_document(src_doc.storage_path)

        try:
            new_doc = self.engine.split_page_range(source, page_range)
            self.engine.save_document(new_doc, output_doc)
        finally:
            self.engine.close_document(source)
            self.engine.close_document(new_doc)

        return self._build_pdf_document(output_doc)

    def merge_pdfs(
        self,
        first_doc: PdfDocument,
        second_doc: PdfDocument,
        output_doc: Path
    ) -> PdfDocument:
        """
        Merges two PDFs into a single document.

        :param first_doc: First PDF.
        :param second_doc: Second PDF.
        :param output_doc: Output file path.
        :return: New PdfDocument.
        """
        first = self.engine.open_document(first_doc.storage_path)
        second = self.engine.open_document(second_doc.storage_path)

        try:
            new_doc = self.engine.merge_pdfs(first, second)
            self.engine.save_document(new_doc, output_doc)
        finally:
            self.engine.close_document(first)
            self.engine.close_document(second)
            self.engine.close_document(new_doc)

        return self._build_pdf_document(output_doc)

    def extract_pages(
        self,
        document: PdfDocument,
        pages: List[int],
        output_doc: Path
    ) -> PdfDocument:
        """
        Extracts specific pages into a new PDF.

        :param document: Source PdfDocument.
        :param pages: List of 1-based page indices.
        :param output_doc: Output file path.
        :return: New PdfDocument.
        """
        source = self.engine.open_document(document.storage_path)

        try:
            new_doc = self.engine.extract_pages(source, pages)
            self.engine.save_document(new_doc, output_doc)
        finally:
            self.engine.close_document(source)
            self.engine.close_document(new_doc)

        return self._build_pdf_document(output_doc)