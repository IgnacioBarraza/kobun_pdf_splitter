from pathlib import Path

import fitz


class PdfEngineAdapter:
    def open_document(self, file_path: Path):
        return fitz.open(file_path)

    def get_page_count(self, document) -> int:
        return document.pageCount

    def extract_text(self, document, page_number: int) -> str:
        page = document.load_page(page_number)
        return page.get_text('text')

    def create_empty_document(self):
        return fitz.open()