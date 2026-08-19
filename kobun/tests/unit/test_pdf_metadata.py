import pytest

from kobun.domain.pdf.exceptions.invalid_pdf_metadata_exception import InvalidPdfMetadataException
from kobun.domain.pdf.value_objects.pdf_metadata import PdfMetadata

def test_pdf_metadata_creation_success():
    meta = PdfMetadata(title="Mi Tesis", author="Ignacio", subject="Entrega Final")
    assert meta.title == "Mi Tesis"
    assert meta.author == "Ignacio"

def test_pdf_metadata_error_empty_title():
    with pytest.raises(InvalidPdfMetadataException, match="Title cannot be empty"):
        PdfMetadata(title="", author="Autor")

def test_pdf_metadata_default_values():
    meta = PdfMetadata(title="Documento Sin Autor", author=None)
    assert meta.author is None
    assert meta.title == "Documento Sin Autor"