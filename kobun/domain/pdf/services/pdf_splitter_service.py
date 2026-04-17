from typing import List, Set

from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException
from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException
from kobun.domain.pdf.value_objects.page_range import PageRange


class PdfSplitterService:
    """
    Servicio de Dominio que centraliza la lógica de negocio compleja para Kobun.
    Este servicio utiliza los métodos definidos en el PdfRepository pero bajo
    reglas de negocio estrictas.
    """

    def validate_document_for_processing(self, document: PdfDocument) -> None:
        """
        Valida si el documento está en un estado que permite su manipulación.
        Usa las reglas definidas en tu entidad PdfDocument.
        """
        if document.page_count is None or document.page_count <= 0:
            raise InvalidPdfException("El documento no tiene páginas válidas para procesar.")

        if not document.storage_path.exists():
            raise InvalidPdfException(f"El archivo físico no existe en: {document.storage_path}")

    def validate_ranges(self, document: PdfDocument, ranges: List[PageRange]) -> None:
        """
        Asegura que todos los rangos solicitados existan dentro del documento.
        """
        self.validate_document_for_processing(document)

        for p_range in ranges:
            if p_range.end > document.page_count:
                raise InvalidPageRangeException(
                    f"Rango fuera de límites: El PDF tiene {document.page_count} páginas, "
                    f"pero se pidió hasta la {p_range.end}."
                )

    def get_pages_to_extract(self, ranges: List[PageRange]) -> List[int]:
        """
        Transforma múltiples objetos PageRange en una lista única de índices
        reales (1-based), ordenada y sin duplicados.
        """
        pages: Set[int] = set()
        for p_range in ranges:
            # Aprovecha el método to_range() que ya tienes en tu Value Object
            pages.update(p_range.to_range())

        return sorted(list(pages))

    def prepare_split_metadata(self, source_doc: PdfDocument, pages: List[int]) -> dict:
        original_meta = source_doc.metadata
        print(original_meta)

        title = original_meta.get('title') if isinstance(original_meta, dict) else getattr(original_meta, 'title',
                                                                                           'Doc')
        author = original_meta.get('author') if isinstance(original_meta, dict) else getattr(original_meta, 'author',
                                                                                             '')

        return {
            "title": f"{title or 'Doc'} (Split)",
            "author": author,
            "subject": f"Extracción de {len(pages)} páginas.",
            "creator": "Kobun PDF Utility"
        }