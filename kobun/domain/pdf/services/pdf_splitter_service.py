from pathlib import PurePath

from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException
from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.domain.pdf.value_objects.pdf_metadata import PdfMetadata

CREATOR_NAME = "Kobun PDF Utility"
PDF_SUFFIX = ".pdf"
FALLBACK_STEM = "kobun_split"

# Caracteres prohibidos en Windows. Se filtran siempre, no sólo en Windows,
# para que un PDF exportado en Linux siga siendo copiable a otro sistema.
_ILLEGAL_FILENAME_CHARS = frozenset('<>:"/\\|?*')


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

    def suggest_output_filename(self, source_doc: PdfDocument, selection: PageSelection) -> str:
        """
        Nombre de archivo propuesto para el resultado: "book.pdf" + "1-5,10-15"
        se convierte en "book_1-5_10-15.pdf".

        Es una regla de negocio (así nombra Kobun sus exportaciones), no una
        decisión de UI, así que vive en el dominio. La UI puede ofrecerlo como
        default editable en el diálogo de guardado.
        """
        stem = self._sanitize_filename(PurePath(source_doc.filename).stem) or FALLBACK_STEM
        suffix = str(selection).replace(",", "_")

        return f"{stem}_{suffix}{PDF_SUFFIX}"

    @staticmethod
    def _sanitize_filename(value: str) -> str:
        """
        Reemplaza caracteres inválidos por "_" y recorta puntos y espacios
        finales, que Windows tampoco acepta.
        """
        cleaned = "".join(
            "_" if char in _ILLEGAL_FILENAME_CHARS or ord(char) < 32 else char
            for char in value
        )
        return cleaned.strip(" .")

    def prepare_split_metadata(self, source_doc: PdfDocument, selection: PageSelection) -> PdfMetadata:
        """
        Construye la metadata del PDF resultante derivándola del original,
        para que el archivo exportado sea trazable hasta su fuente.

        El título nunca lleva la extensión: es un título de documento, no un
        nombre de archivo. El `subject` sí conserva el nombre completo, porque
        ahí lo que importa es poder identificar el archivo de origen.
        """
        source_meta = source_doc.metadata
        base = source_meta.title or PurePath(source_doc.filename).stem

        return PdfMetadata(
            title=f"{base} ({selection})",
            author=source_meta.author,
            subject=f"Páginas {selection} extraídas de {source_doc.filename}",
            keywords=source_meta.keywords,
            creator=CREATOR_NAME,
            producer=source_meta.producer,
        )
