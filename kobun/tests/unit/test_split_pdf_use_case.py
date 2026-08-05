from pathlib import Path
from typing import List, Optional

import pytest

from kobun.application.interfaces.pdf_repository import PdfRepository
from kobun.application.use_cases.split_pdf_use_case import SplitPdfUseCase
from kobun.domain.pdf.entities.pdf_document import PdfDocument, PdfProcessingStatus
from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService
from kobun.domain.pdf.value_objects.page_range import PageRange
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.domain.pdf.value_objects.pdf_metadata import PdfMetadata


class FakePdfRepository(PdfRepository):
    """
    Doble de prueba en memoria: permite testear la orquestación del use case
    sin depender de PyMuPDF ni escribir archivos.
    """

    def __init__(self, source: PdfDocument, result: PdfDocument, fail_on_split: bool = False):
        self._source = source
        self._result = result
        self._fail_on_split = fail_on_split
        self.received_selection: Optional[PageSelection] = None
        self.received_metadata: Optional[PdfMetadata] = None

    def open_document(self, file_path: Path) -> PdfDocument:
        return self._source

    def split_page_selection(self, src_doc, output_doc, selection, metadata=None) -> PdfDocument:
        if self._fail_on_split:
            raise RuntimeError("engine exploded")
        self.received_selection = selection
        self.received_metadata = metadata
        return self._result

    # --- No usados por este use case ---
    def close_document(self, document: PdfDocument) -> None: ...

    def get_page_count(self, document: PdfDocument) -> int: ...

    def extract_metadata(self, document: PdfDocument) -> PdfMetadata: ...

    def extract_text(self, document: PdfDocument, page_number: int) -> str: ...

    def split_single_page(self, src_doc, output_doc: Path, page_index: int) -> PdfDocument: ...

    def split_page_range(self, src_doc, output_doc: Path, page_range: PageRange) -> PdfDocument: ...

    def merge_pdfs(self, first_doc, second_doc, output_doc: Path) -> PdfDocument: ...

    def extract_pages(self, document, pages: List[int], output_doc: Path) -> PdfDocument: ...


@pytest.fixture
def scenario(make_pdf_document):
    def _build(page_count: int = 100, fail_on_split: bool = False):
        source = make_pdf_document(filename="book.pdf", page_count=page_count)
        result = make_pdf_document(filename="book_split.pdf", page_count=11)
        repository = FakePdfRepository(source, result, fail_on_split=fail_on_split)
        use_case = SplitPdfUseCase(repository, PdfSplitterService())
        return use_case, repository, source, result

    return _build


def test_execute_returns_result_and_marks_source_as_processed(scenario):
    use_case, repository, source, expected = scenario()
    selection = PageSelection.parse("1-5,10-15")

    result = use_case.execute(Path("book.pdf"), Path("out.pdf"), selection)

    assert result is expected
    assert source.status == PdfProcessingStatus.PROCESSED
    assert source.processed_at is not None
    assert source.page_count == 100, "El conteo del origen no debe sobrescribirse con el del resultado"
    assert repository.received_selection == selection


def test_execute_passes_derived_metadata_to_repository(scenario):
    use_case, repository, source, _ = scenario()

    use_case.execute(Path("book.pdf"), Path("out.pdf"), PageSelection.parse("10-20"))

    assert repository.received_metadata is not None
    assert repository.received_metadata.title == "Mi Tesis (10-20)"


def test_execute_rejects_selection_beyond_document(scenario):
    use_case, repository, source, _ = scenario(page_count=10)

    with pytest.raises(InvalidPageRangeException):
        use_case.execute(Path("book.pdf"), Path("out.pdf"), PageSelection.parse("1-50"))

    assert source.status == PdfProcessingStatus.UPLOADED, "Validar no debe alterar el estado"
    assert repository.received_selection is None


def test_execute_marks_source_as_failed_and_propagates_engine_error(scenario):
    use_case, _, source, _ = scenario(fail_on_split=True)

    with pytest.raises(RuntimeError, match="engine exploded"):
        use_case.execute(Path("book.pdf"), Path("out.pdf"), PageSelection.parse("1-5"))

    assert source.status == PdfProcessingStatus.FAILED
