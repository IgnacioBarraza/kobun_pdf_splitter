from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException
from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.domain.pdf.value_objects.pdf_metadata import PdfMetadata

CREATOR_NAME = "Kobun PDF Utility"


class PdfSplitterService:
    """
    Servicio de Dominio que centraliza las reglas de negocio del split.

    No conoce PyMuPDF ni el sistema de archivos más allá de comprobar la
    existencia del documento: sólo decide qué operaciones son lícitas y
    cómo debe quedar la metadata del resultado.
    """

    def validate_document_for_processing(self, document: PdfDocument) -> None:
        """
        Valida si el documento está en un estado que permite su manipulación.
        """
        if document.page_count is None or document.page_count <= 0:
            raise InvalidPdfException("El documento no tiene páginas válidas para procesar.")

        if not document.storage_path.exists():
            raise InvalidPdfException(f"El archivo físico no existe en: {document.storage_path}")

    def validate_selection(self, document: PdfDocument, selection: PageSelection) -> None:
        """
        Asegura que todas las páginas solicitadas existan dentro del documento.
        """
        self.validate_document_for_processing(document)

        if selection.max_page > document.page_count:
            raise InvalidPageRangeException(
                f"Rango fuera de límites: El PDF tiene {document.page_count} páginas, "
                f"pero se pidió hasta la {selection.max_page}."
            )

    def prepare_split_metadata(self, source_doc: PdfDocument, selection: PageSelection) -> PdfMetadata:
        """
        Construye la metadata del PDF resultante derivándola del original,
        para que el archivo exportado sea trazable hasta su fuente.
        """
        source_meta = source_doc.metadata

        return PdfMetadata(
            title=f"{source_meta.title or source_doc.filename} ({selection})",
            author=source_meta.author,
            subject=f"Páginas {selection} extraídas de {source_doc.filename}",
            keywords=source_meta.keywords,
            creator=CREATOR_NAME,
            producer=source_meta.producer,
        )
