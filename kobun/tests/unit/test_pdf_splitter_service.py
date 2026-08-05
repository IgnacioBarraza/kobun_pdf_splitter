import pytest

from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException
from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException
from kobun.domain.pdf.services.pdf_splitter_service import CREATOR_NAME, PdfSplitterService
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.domain.pdf.value_objects.pdf_metadata import PdfMetadata


@pytest.fixture
def service():
    return PdfSplitterService()


def test_selection_within_document_is_valid(service, make_pdf_document):
    document = make_pdf_document(page_count=100)
    service.validate_selection(document, PageSelection.parse("1-5,90-100"))


def test_selection_beyond_last_page_is_rejected(service, make_pdf_document):
    document = make_pdf_document(page_count=100)

    with pytest.raises(InvalidPageRangeException, match="Rango fuera de límites"):
        service.validate_selection(document, PageSelection.parse("1-5,99-101"))


def test_document_without_pages_is_rejected(service, make_pdf_document):
    document = make_pdf_document(page_count=0)

    with pytest.raises(InvalidPdfException, match="no tiene páginas válidas"):
        service.validate_selection(document, PageSelection.parse("1"))


def test_missing_file_is_rejected(service, make_pdf_document):
    document = make_pdf_document()
    document.storage_path.unlink()

    with pytest.raises(InvalidPdfException, match="no existe"):
        service.validate_selection(document, PageSelection.parse("1"))


def test_split_metadata_derives_from_source(service, make_pdf_document):
    document = make_pdf_document(
        filename="tesis.pdf",
        metadata=PdfMetadata(title="Mi Tesis", author="Ignacio", keywords="derecho"),
    )

    result = service.prepare_split_metadata(document, PageSelection.parse("10-20"))

    assert result.title == "Mi Tesis (10-20)"
    assert result.author == "Ignacio"
    assert result.keywords == "derecho"
    assert result.creator == CREATOR_NAME
    assert "tesis.pdf" in result.subject


def test_split_metadata_falls_back_to_filename_when_title_missing(service, make_pdf_document):
    document = make_pdf_document(
        filename="sin_titulo.pdf",
        metadata=PdfMetadata(author="Ignacio"),
    )

    result = service.prepare_split_metadata(document, PageSelection.parse("1-2"))

    assert result.title == "sin_titulo.pdf (1-2)"


def test_split_metadata_reflects_discontinuous_selection(service, make_pdf_document):
    document = make_pdf_document(metadata=PdfMetadata(title="Manual"))

    result = service.prepare_split_metadata(document, PageSelection.parse("1-5,10"))

    assert result.title == "Manual (1-5,10)"
