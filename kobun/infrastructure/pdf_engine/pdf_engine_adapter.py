from pathlib import Path
from typing import Dict, List, Optional, Sequence

import pymupdf
from pymupdf import Document

from kobun.domain.pdf.value_objects.page_range import PageRange

# Claves de metadata que entiende PyMuPDF y que Kobun sabe escribir.
_METADATA_KEYS = ("title", "author", "subject", "keywords", "creator", "producer")


class PdfEngineAdapter:
    """
    Envoltura delgada sobre PyMuPDF.

    Convención de índices: todos los métodos públicos reciben páginas
    **1-based** e inclusivas, igual que el dominio y la UI. La traducción al
    0-based de PyMuPDF ocurre exclusivamente dentro de esta clase.
    """

    def open_document(self, file_path: Path) -> Document:
        return pymupdf.open(file_path)

    def close_document(self, document: Document) -> None:
        document.close()

    def get_page_count(self, document: Document) -> int:
        return document.page_count

    def needs_password(self, document: Document) -> bool:
        """
        True si el documento está cifrado y no se aportó la contraseña.
        """
        return bool(document.needs_pass)

    def is_pdf(self, document: Document) -> bool:
        """
        PyMuPDF abre también XPS, EPUB, CBZ e imágenes. Kobun sólo trabaja con
        PDFs, así que hay que preguntar explícitamente.
        """
        return bool(document.is_pdf)

    def extract_metadata(self, document: Document) -> Dict[str, Optional[str]]:
        return document.metadata

    def set_metadata(self, document: Document, metadata: Dict[str, Optional[str]]) -> None:
        """
        Escribe metadata en el documento, ignorando claves desconocidas o vacías.
        """
        payload = {
            key: value
            for key, value in metadata.items()
            if key in _METADATA_KEYS and value
        }
        document.set_metadata(payload)

    def extract_text(self, document: Document, page_number: int) -> str:
        """
        :param page_number: Página 1-based.
        """
        page = document.load_page(page_number - 1)
        return page.get_text("text")

    def create_empty_document(self) -> Document:
        return pymupdf.open()

    def split_single_page(self, src_doc: Document, page_index: int) -> Document:
        """
        :param page_index: Página 1-based a extraer.
        """
        return self.extract_page_ranges(src_doc, [PageRange(start=page_index, end=page_index)])

    def split_page_range(self, src_doc: Document, page_range: PageRange) -> Document:
        return self.extract_page_ranges(src_doc, [page_range])

    def extract_page_ranges(self, src_doc: Document, ranges: Sequence[PageRange]) -> Document:
        """
        Copia varios rangos contiguos a un documento nuevo, en el orden recibido.

        Usa una sola inserción por rango en lugar de una por página, así extraer
        "1-500" cuesta una operación y no quinientas.
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
        :param pages: Páginas 1-based, en el orden en que deben quedar.
        """
        new_doc = self.create_empty_document()

        for page in pages:
            if page < 1 or page > document.page_count:
                raise ValueError(f"Invalid page number: {page}")

            new_doc.insert_pdf(document, from_page=page - 1, to_page=page - 1)
        return new_doc

    def save_document(self, document: Document, path: Path) -> None:
        document.save(path)
