from pathlib import Path
from typing import Dict, List, Optional, Sequence

import pymupdf
from pymupdf import Document

from kobun.domain.pdf.value_objects.page_range import PageRange

# Metadata keys PyMuPDF understands and Kobun knows how to write.
_METADATA_KEYS = ("title", "author", "subject", "keywords", "creator", "producer")


class PdfEngineAdapter:
    """
    A thin wrapper over PyMuPDF.

    Index convention: every public method takes **1-based**, inclusive pages,
    same as the domain and the UI. Translating to PyMuPDF's 0-based indices
    happens exclusively inside this class.
    """

    def open_document(self, file_path: Path) -> Document:
        return pymupdf.open(file_path)

    def close_document(self, document: Document) -> None:
        document.close()

    def get_page_count(self, document: Document) -> int:
        return document.page_count

    def needs_password(self, document: Document) -> bool:
        """
        True if the document is encrypted and no password was supplied.
        """
        return bool(document.needs_pass)

    def is_pdf(self, document: Document) -> bool:
        """
        PyMuPDF also opens XPS, EPUB, CBZ and images. Kobun only works with
        PDFs, so it has to ask explicitly.
        """
        return bool(document.is_pdf)

    def extract_metadata(self, document: Document) -> Dict[str, Optional[str]]:
        return document.metadata

    def set_metadata(self, document: Document, metadata: Dict[str, Optional[str]]) -> None:
        """
        Writes metadata into the document, ignoring unknown or empty keys.
        """
        payload = {
            key: value
            for key, value in metadata.items()
            if key in _METADATA_KEYS and value
        }
        document.set_metadata(payload)

    def extract_text(self, document: Document, page_number: int) -> str:
        """
        :param page_number: 1-based page.
        """
        page = document.load_page(page_number - 1)
        return page.get_text("text")

    def create_empty_document(self) -> Document:
        return pymupdf.open()

    def split_single_page(self, src_doc: Document, page_index: int) -> Document:
        """
        :param page_index: 1-based page to extract.
        """
        return self.extract_page_ranges(src_doc, [PageRange(start=page_index, end=page_index)])

    def split_page_range(self, src_doc: Document, page_range: PageRange) -> Document:
        return self.extract_page_ranges(src_doc, [page_range])

    def extract_page_ranges(self, src_doc: Document, ranges: Sequence[PageRange]) -> Document:
        """
        Copies several contiguous ranges into a new document, in the order
        received.

        It uses one insertion per range instead of one per page, so extracting
        "1-500" costs one operation rather than five hundred.
        """
        new_doc = self.create_empty_document()

        for p_range in ranges:
            if p_range.end > src_doc.page_count:
                raise ValueError(
                    f"Page range {p_range} exceeds document length ({src_doc.page_count} pages)."
                )
            new_doc.insert_pdf(src_doc, from_page=p_range.start - 1, to_page=p_range.end - 1)

        return new_doc

    def merge_pdfs(self, first_doc: Document, second_doc: Document) -> Document:
        new_doc = self.create_empty_document()
        new_doc.insert_pdf(first_doc)
        new_doc.insert_pdf(second_doc)
        return new_doc

    def extract_pages(self, document: Document, pages: List[int]) -> Document:
        """
        :param pages: 1-based pages, in the order they should end up in.
        """
        new_doc = self.create_empty_document()

        for page in pages:
            if page < 1 or page > document.page_count:
                raise ValueError(f"Invalid page number: {page}")

            new_doc.insert_pdf(document, from_page=page - 1, to_page=page - 1)
        return new_doc

    def save_document(self, document: Document, path: Path) -> None:
        document.save(path)
