from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict

from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.value_objects.page_range import PageRange


class PdfRepository(ABC):
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
    def create_empty_document(self) -> PdfDocument:
        pass

    @abstractmethod
    def extract_metadata(self, document: PdfDocument) -> Dict[str, str]:
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
    def merge_pdfs(self, first_doc: PdfDocument, second_doc: PdfDocument, output_doc: Path) -> PdfDocument:
        pass

    @abstractmethod
    def extract_pages(self, document: PdfDocument, pages: List[int], output_doc: Path) -> PdfDocument:
        pass