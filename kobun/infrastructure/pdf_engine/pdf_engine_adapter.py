from pathlib import Path
from typing import Dict, List

import fitz
from pymupdf import Document

from kobun.domain.pdf.value_objects.page_range import PageRange


class PdfEngineAdapter:
    def open_document(self, file_path: Path) -> Document:
        return fitz.open(file_path)

    def close_document(self, document: Document) -> None:
        document.close()

    def get_page_count(self, document: Document) -> int:
        return document.page_count

    def extract_metadata(self, document: Document) -> Dict[str, str | None]:
        return document.metadata

    def extract_text(self, document: Document, page_number: int) -> str:
        page = document.load_page(page_number)
        return page.get_text('text')

    def create_empty_document(self) -> Document:
        return fitz.open()

    def split_single_page(self, src_doc: Document, page_index: int) -> Document:
        new_doc = self.create_empty_document()
        new_doc.insert_pdf(src_doc, from_page= page_index - 1, to_page = page_index - 1)

        return new_doc

    def split_page_range(self, src_doc: Document, page_range: PageRange) -> Document:
        new_doc = self.create_empty_document()
        new_doc.insert_pdf(src_doc, from_page = page_range.start -1, to_page = page_range.end - 1)

        return new_doc

    def merge_pdfs(self, first_doc: Document, second_doc: Document) -> Document:
        new_doc = self.create_empty_document()
        new_doc.insert_pdf(first_doc)
        new_doc.insert_pdf(second_doc)
        return new_doc

    def extract_pages(self, document: Document, pages: List[int]) -> Document:
        new_doc = self.create_empty_document()

        for page in pages:
            if page < 1 or page > document.page_count:
                raise ValueError(f"Invalid page number: {page}")

            new_doc.insert_pdf(document, from_page=page - 1, to_page=page - 1)
        return new_doc

    def save_document(self, document: Document, path: Path) -> None:
        document.save(path)