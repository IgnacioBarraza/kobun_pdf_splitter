from pathlib import PurePath

from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException
from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.domain.pdf.value_objects.pdf_metadata import PdfMetadata

CREATOR_NAME = "Kobun PDF Utility"
PDF_SUFFIX = ".pdf"
FALLBACK_STEM = "kobun_split"

# Characters Windows forbids. Filtered always, not only on Windows, so a PDF
# exported on Linux stays copyable to another system.
_ILLEGAL_FILENAME_CHARS = frozenset('<>:"/\\|?*')


class PdfSplitterService:
    """
    Domain Service holding the business rules of splitting.

    It knows neither PyMuPDF nor the filesystem beyond checking that the
    document exists: it only decides which operations are legitimate and what
    the resulting metadata should look like.
    """

    def validate_document_for_processing(self, document: PdfDocument) -> None:
        """
        Checks the document is in a state that allows manipulation.
        """
        if document.page_count is None or document.page_count <= 0:
            raise InvalidPdfException("El documento no tiene páginas válidas para procesar.")

        if not document.storage_path.exists():
            raise InvalidPdfException(f"El archivo físico no existe en: {document.storage_path}")

    def validate_selection(self, document: PdfDocument, selection: PageSelection) -> None:
        """
        Ensures every requested page exists within the document.
        """
        self.validate_document_for_processing(document)

        if selection.max_page > document.page_count:
            raise InvalidPageRangeException(
                f"Rango fuera de límites: El PDF tiene {document.page_count} páginas, "
                f"pero se pidió hasta la {selection.max_page}."
            )

    def suggest_output_filename(self, source_doc: PdfDocument, selection: PageSelection) -> str:
        """
        Suggested filename for the result: "book.pdf" + "1-5,10-15" becomes
        "book_1-5_10-15.pdf".

        This is a business rule —how Kobun names its exports— and not a UI
        decision, so it lives in the domain. The UI can offer it as an editable
        default in the save dialog.
        """
        stem = self._sanitize_filename(PurePath(source_doc.filename).stem) or FALLBACK_STEM
        suffix = str(selection).replace(",", "_")

        return f"{stem}_{suffix}{PDF_SUFFIX}"

    @staticmethod
    def _sanitize_filename(value: str) -> str:
        """
        Replaces invalid characters with "_" and trims trailing dots and
        spaces, which Windows does not accept either.
        """
        cleaned = "".join(
            "_" if char in _ILLEGAL_FILENAME_CHARS or ord(char) < 32 else char
            for char in value
        )
        return cleaned.strip(" .")

    def prepare_split_metadata(self, source_doc: PdfDocument, selection: PageSelection) -> PdfMetadata:
        """
        Builds the resulting PDF's metadata by deriving it from the original,
        so the exported file is traceable back to its source.

        The title never carries the extension: it is a document title, not a
        filename. The `subject` does keep the full name, because there what
        matters is being able to identify the source file.
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
