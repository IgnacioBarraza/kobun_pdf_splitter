import pytest

from kobun.domain.pdf.entities.pdf_document import PdfDocument, PdfProcessingStatus
from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException
from kobun.domain.pdf.value_objects.pdf_metadata import PdfMetadata


def test_new_document_starts_as_uploaded(make_pdf_document):
    document = make_pdf_document()
    assert document.status == PdfProcessingStatus.UPLOADED
    assert document.processed_at is None


def test_lifecycle_uploaded_to_processed(make_pdf_document):
    document = make_pdf_document(page_count=50)

    document.mark_as_processing()
    assert document.status == PdfProcessingStatus.PROCESSING

    document.mark_as_processed()
    assert document.status == PdfProcessingStatus.PROCESSED
    assert document.processed_at is not None
    assert document.page_count == 50


def test_mark_as_processed_updates_page_count_when_provided(make_pdf_document):
    document = make_pdf_document(page_count=50)
    document.mark_as_processing()
    document.mark_as_processed(page_count=12)
    assert document.page_count == 12


def test_cannot_process_twice(make_pdf_document):
    document = make_pdf_document()
    document.mark_as_processing()

    with pytest.raises(InvalidPdfException, match="Only uploaded documents"):
        document.mark_as_processing()


def test_cannot_mark_as_processed_without_processing(make_pdf_document):
    document = make_pdf_document()

    with pytest.raises(InvalidPdfException, match="must be processing"):
        document.mark_as_processed()


def test_mark_as_failed_from_any_state(make_pdf_document):
    document = make_pdf_document()
    document.mark_as_failed()
    assert document.status == PdfProcessingStatus.FAILED


def test_rename_requires_pdf_extension(make_pdf_document):
    document = make_pdf_document()

    document.rename("tesis_final.pdf")
    assert document.filename == "tesis_final.pdf"

    with pytest.raises(InvalidPdfException, match="must end with .pdf"):
        document.rename("tesis_final.docx")


def test_invariants_rejected_at_creation(tmp_path):
    metadata = PdfMetadata(title="Doc")
    path = tmp_path / "doc.pdf"
    path.write_bytes(b"x")

    with pytest.raises(InvalidPdfException, match="must end with .pdf"):
        PdfDocument(filename="doc.txt", storage_path=path, size_bytes=1, checksum="abc", metadata=metadata)

    with pytest.raises(InvalidPdfException, match="File size"):
        PdfDocument(filename="doc.pdf", storage_path=path, size_bytes=0, checksum="abc", metadata=metadata)

    with pytest.raises(InvalidPdfException, match="Checksum"):
        PdfDocument(filename="doc.pdf", storage_path=path, size_bytes=1, checksum="", metadata=metadata)


def test_equality_is_by_identity_not_by_value(make_pdf_document):
    first = make_pdf_document()
    second = make_pdf_document()

    assert first != second
    assert first == first
    assert len({first, second, first}) == 2
