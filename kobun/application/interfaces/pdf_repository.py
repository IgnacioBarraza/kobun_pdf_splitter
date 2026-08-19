from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.value_objects.page_range import PageRange
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.domain.pdf.value_objects.pdf_metadata import PdfMetadata


class PdfRepository(ABC):
    """
    Contrato de manipulación de PDFs visto desde el dominio.

    Todos los índices de página son 1-based, igual que en PageRange y en la UI.
    Cada implementación es responsable de traducirlos al motor que use.
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
        Extrae una selección de rangos, posiblemente discontinua, a un nuevo PDF.
        """
        pass

    @abstractmethod
    def merge_pdfs(self, first_doc: PdfDocument, second_doc: PdfDocument, output_doc: Path) -> PdfDocument:
        pass

    @abstractmethod
    def extract_pages(self, document: PdfDocument, pages: List[int], output_doc: Path) -> PdfDocument:
        pass
