from pathlib import Path
from typing import List

import pytest

from kobun.application.interfaces.pdf_repository import PdfRepository
from kobun.application.use_cases.load_pdf_use_case import LoadPdfUseCase
from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.exceptions.encrypted_pdf_exception import EncryptedPdfException
from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException
from kobun.domain.pdf.exceptions.pdf_not_found_exception import PdfNotFoundException
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService
from kobun.domain.pdf.value_objects.page_range import PageRange
from kobun.domain.pdf.value_objects.pdf_metadata import PdfMetadata


class StubPdfRepository(PdfRepository):
    """Returns a fixed document, or raises whichever exception it is given."""

    def __init__(self, document: PdfDocument = None, error: Exception = None):
        self._document = document
        self._error = error
        self.received_path: Path = None

    def open_document(self, file_path: Path) -> PdfDocument:
        self.received_path = file_path
        if self._error is not None:
            raise self._error
        return self._document

    def close_document(self, document: PdfDocument) -> None: ...

    def get_page_count(self, document: PdfDocument) -> int: ...

    def extract_metadata(self, document: PdfDocument) -> PdfMetadata: ...

    def extract_text(self, document: PdfDocument, page_number: int) -> str: ...

    def split_single_page(self, src_doc, output_doc: Path, page_index: int) -> PdfDocument: ...

    def split_page_range(self, src_doc, output_doc: Path, page_range: PageRange) -> PdfDocument: ...

    def split_page_selection(self, src_doc, output_doc, selection, metadata=None) -> PdfDocument: ...

    def merge_pdfs(self, first_doc, second_doc, output_doc: Path) -> PdfDocument: ...

    def extract_pages(self, document, pages: List[int], output_doc: Path) -> PdfDocument: ...


def build_use_case(document=None, error=None):
    repository = StubPdfRepository(document=document, error=error)
    return LoadPdfUseCase(repository, PdfSplitterService()), repository


def test_returns_the_loaded_document(make_pdf_document):
    document = make_pdf_document(filename="tesis.pdf", page_count=340)
    use_case, _ = build_use_case(document)

    result = use_case.execute(document.storage_path)

    assert result is document
    assert result.page_count == 340
    assert result.metadata.title == "Mi Tesis"


def test_accepts_a_string_path(make_pdf_document):
    document = make_pdf_document()
    use_case, repository = build_use_case(document)

    use_case.execute(str(document.storage_path))

    assert repository.received_path == document.storage_path
    assert isinstance(repository.received_path, Path)


def test_propagates_not_found():
    use_case, _ = build_use_case(error=PdfNotFoundException("no existe"))

    with pytest.raises(PdfNotFoundException):
        use_case.execute(Path("fantasma.pdf"))


def test_propagates_encrypted():
    use_case, _ = build_use_case(error=EncryptedPdfException("con contraseña"))

    with pytest.raises(EncryptedPdfException):
        use_case.execute(Path("protegido.pdf"))


def test_load_errors_share_a_single_base_exception():
    """
    The UI needs a single `except` for every loading failure; the specific
    cases exist only to give better messages.
    """
    assert issubclass(PdfNotFoundException, InvalidPdfException)
    assert issubclass(EncryptedPdfException, InvalidPdfException)


def test_rejects_a_document_without_pages(make_pdf_document):
    use_case, _ = build_use_case(make_pdf_document(page_count=0))

    with pytest.raises(InvalidPdfException, match="no tiene páginas válidas"):
        use_case.execute(Path("vacio.pdf"))


def test_rejects_a_document_whose_file_disappeared(make_pdf_document):
    document = make_pdf_document()
    document.storage_path.unlink()
    use_case, _ = build_use_case(document)

    with pytest.raises(InvalidPdfException, match="no existe"):
        use_case.execute(document.storage_path)
