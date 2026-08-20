import pytest

from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.value_objects.pdf_metadata import PdfMetadata


@pytest.fixture
def make_pdf_document(tmp_path):
    """
    Factory of PdfDocument entities backed by a real file on disk, so the
    validations that check for the file's existence pass.
    """

    def _make(filename: str = "book.pdf", page_count: int = 100, metadata: PdfMetadata = None) -> PdfDocument:
        path = tmp_path / filename
        path.write_bytes(b"%PDF-1.7 fake content")

        return PdfDocument(
            filename=filename,
            storage_path=path,
            size_bytes=path.stat().st_size,
            checksum="deadbeef",
            metadata=metadata or PdfMetadata(title="Mi Tesis", author="Ignacio"),
            page_count=page_count,
        )

    return _make
