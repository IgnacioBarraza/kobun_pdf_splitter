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


def test_split_metadata_falls_back_to_filename_without_its_extension(service, make_pdf_document):
    """
    The title is a document title, not a filename: dragging the ".pdf" along
    produced things like "contrato.pdf (3-6)" in what was exported.
    """
    document = make_pdf_document(
        filename="sin_titulo.pdf",
        metadata=PdfMetadata(author="Ignacio"),
    )

    result = service.prepare_split_metadata(document, PageSelection.parse("1-2"))

    assert result.title == "sin_titulo (1-2)"
    assert ".pdf" not in result.title


def test_split_metadata_keeps_dots_that_belong_to_the_name(service, make_pdf_document):
    """Only the last extension is dropped, not everything after a dot."""
    document = make_pdf_document(
        filename="2026.03.01_Contrato_Indefinido.pdf",
        metadata=PdfMetadata(author="Ignacio"),
    )

    result = service.prepare_split_metadata(document, PageSelection.parse("3-6"))

    assert result.title == "2026.03.01_Contrato_Indefinido (3-6)"


def test_split_metadata_subject_keeps_the_full_filename(service, make_pdf_document):
    """
    In the subject the full name does matter: it serves to identify the source
    file on disk.
    """
    document = make_pdf_document(filename="contrato.pdf", metadata=PdfMetadata(author="I"))

    result = service.prepare_split_metadata(document, PageSelection.parse("1"))

    assert "contrato.pdf" in result.subject


def test_split_metadata_reflects_discontinuous_selection(service, make_pdf_document):
    document = make_pdf_document(metadata=PdfMetadata(title="Manual"))

    result = service.prepare_split_metadata(document, PageSelection.parse("1-5,10"))

    assert result.title == "Manual (1-5,10)"


def test_suggested_filename_combines_stem_and_selection(service, make_pdf_document):
    document = make_pdf_document(filename="book.pdf")

    assert service.suggest_output_filename(document, PageSelection.parse("1-5")) == "book_1-5.pdf"


def test_suggested_filename_replaces_commas_with_underscores(service, make_pdf_document):
    document = make_pdf_document(filename="book.pdf")

    result = service.suggest_output_filename(document, PageSelection.parse("1-5,10-15,20"))

    assert result == "book_1-5_10-15_20.pdf"


def test_suggested_filename_uses_canonical_selection(service, make_pdf_document):
    """Overlapping ranges merge before naming, so "1-5,3-8" yields "1-8"."""
    document = make_pdf_document(filename="book.pdf")

    assert service.suggest_output_filename(document, PageSelection.parse("1-5,3-8")) == "book_1-8.pdf"


def test_suggested_filename_strips_filesystem_hostile_characters(service, make_pdf_document):
    document = make_pdf_document(filename='re:porte "final"?.pdf')

    result = service.suggest_output_filename(document, PageSelection.parse("3"))

    # Every invalid character becomes one "_", with no collapsing of runs: that
    # keeps the resulting name predictable from the original.
    assert result == "re_porte _final___3.pdf"
    assert not set(result) & set('<>:"/\\|?*')


def test_suggested_filename_falls_back_when_stem_is_unusable(service, make_pdf_document):
    document = make_pdf_document(filename=" .pdf")

    assert service.suggest_output_filename(document, PageSelection.parse("7")) == "kobun_split_7.pdf"
