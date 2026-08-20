from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.value_objects.page_range import PageRange
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.domain.pdf.value_objects.pdf_metadata import PdfMetadata


class PdfRepository(ABC):
    """
    The PDF manipulation contract as the domain sees it.

    Every page index is 1-based, same as in PageRange and in the UI. Each
    implementation is responsible for translating them to whatever engine it
    uses.
    """

    @abstractmethod
    def open_document(self, file_path: Path) -> PdfDocument:
        pass

    @abstractmethod
    def close_document(self, document: PdfDocument) -> None:
        pass

    @abstractmethod
    def get_page_count(self, document: PdfDocument) -> int:
        pass

    @abstractmethod
    def extract_metadata(self, document: PdfDocument) -> PdfMetadata:
        pass

    @abstractmethod
    def extract_text(self, document: PdfDocument, page_number: int) -> str:
        pass

    @abstractmethod
    def split_single_page(self, src_doc: PdfDocument, output_doc: Path, page_index: int) -> PdfDocument:
        pass

    @abstractmethod
    def split_page_range(self, src_doc: PdfDocument, output_doc: Path, page_range: PageRange) -> PdfDocument:
        pass

    @abstractmethod
    def split_page_selection(
        self,
        src_doc: PdfDocument,
        output_doc: Path,
        selection: PageSelection,
        metadata: Optional[PdfMetadata] = None,
    ) -> PdfDocument:
        """
        Extracts a selection of ranges, possibly discontinuous, into a new PDF.
        """
        pass

    @abstractmethod
    def merge_pdfs(self, first_doc: PdfDocument, second_doc: PdfDocument, output_doc: Path) -> PdfDocument:
        pass

    @abstractmethod
    def extract_pages(self, document: PdfDocument, pages: List[int], output_doc: Path) -> PdfDocument:
        pass
