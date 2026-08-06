from pathlib import Path
from typing import List, Optional

import pytest

from kobun.application.dto.split_pdf_request import SplitPdfRequest
from kobun.application.interfaces.pdf_repository import PdfRepository
from kobun.application.services.output_path_resolver import OutputPathResolver
from kobun.application.use_cases.split_pdf_use_case import SplitPdfUseCase
from kobun.domain.pdf.entities.pdf_document import PdfDocument, PdfProcessingStatus
from kobun.domain.pdf.exceptions.invalid_output_path_exception import InvalidOutputPathException
from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService
from kobun.domain.pdf.value_objects.overwrite_policy import OverwritePolicy
from kobun.domain.pdf.value_objects.page_range import PageRange
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.domain.pdf.value_objects.pdf_metadata import PdfMetadata
from kobun.infrastructure.filesystem.local_file_storage import LocalFileStorage


class FakePdfRepository(PdfRepository):
    """
    Doble de prueba en memoria: permite testear la orquestación del use case
    sin depender de PyMuPDF ni escribir PDFs reales.
    """

    def __init__(self, source: PdfDocument, result: PdfDocument, fail_on_split: bool = False):
        self._source = source
        self._result = result
        self._fail_on_split = fail_on_split
        self.received_selection: Optional[PageSelection] = None
        self.received_metadata: Optional[PdfMetadata] = None
        self.received_output: Optional[Path] = None

    def open_document(self, file_path: Path) -> PdfDocument:
        return self._source

    def split_page_selection(self, src_doc, output_doc, selection, metadata=None) -> PdfDocument:
        if self._fail_on_split:
            raise RuntimeError("engine exploded")

        self.received_selection = selection
        self.received_metadata = metadata
        self.received_output = output_doc
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
        use_case = SplitPdfUseCase(
            repository,
            PdfSplitterService(),
            OutputPathResolver(LocalFileStorage()),
        )
        return use_case, repository, source, result

    return _build


def test_execute_returns_result_and_marks_source_as_processed(scenario):
    use_case, repository, source, expected = scenario()
    selection = PageSelection.parse("1-5,10-15")

    response = use_case.execute(SplitPdfRequest(source.storage_path, selection))

    assert response.output_path == expected.storage_path
    assert response.page_count == expected.page_count
    assert response.selection == selection
    assert source.status == PdfProcessingStatus.PROCESSED
    assert source.processed_at is not None
    assert source.page_count == 100, "El conteo del origen no debe sobrescribirse con el del resultado"
    assert repository.received_selection == selection


def test_execute_passes_derived_metadata_to_repository(scenario):
    use_case, repository, source, _ = scenario()

    use_case.execute(SplitPdfRequest(source.storage_path, PageSelection.parse("10-20")))

    assert repository.received_metadata is not None
    assert repository.received_metadata.title == "Mi Tesis (10-20)"


def test_output_path_defaults_to_suggested_name_next_to_the_source(scenario):
    use_case, repository, source, _ = scenario()

    use_case.execute(SplitPdfRequest(source.storage_path, PageSelection.parse("1-5,10-15")))

    assert repository.received_output == source.storage_path.parent / "book_1-5_10-15.pdf"


def test_explicit_output_file_is_respected(scenario, tmp_path):
    use_case, repository, source, _ = scenario()
    destino = tmp_path / "mi_capitulo.pdf"

    use_case.execute(SplitPdfRequest(source.storage_path, PageSelection.parse("1-5"), output_path=destino))

    assert repository.received_output == destino


def test_output_directory_receives_the_suggested_filename(scenario, tmp_path):
    use_case, repository, source, _ = scenario()
    directorio = tmp_path / "exports"
    directorio.mkdir()

    use_case.execute(SplitPdfRequest(source.storage_path, PageSelection.parse("1-5"), output_path=directorio))

    assert repository.received_output == directorio / "book_1-5.pdf"


def test_existing_output_aborts_before_touching_the_document(scenario, tmp_path):
    use_case, repository, source, _ = scenario()
    ocupado = tmp_path / "ocupado.pdf"
    ocupado.write_bytes(b"previo")

    with pytest.raises(InvalidOutputPathException, match="ya existe"):
        use_case.execute(SplitPdfRequest(source.storage_path, PageSelection.parse("1-5"), output_path=ocupado))

    assert source.status == PdfProcessingStatus.UPLOADED, "Una ruta inválida no es un intento fallido"
    assert repository.received_output is None


def test_rename_policy_resolves_a_free_name(scenario, tmp_path):
    use_case, repository, source, _ = scenario()
    ocupado = tmp_path / "ocupado.pdf"
    ocupado.write_bytes(b"previo")

    use_case.execute(SplitPdfRequest(
        source.storage_path,
        PageSelection.parse("1-5"),
        output_path=ocupado,
        policy=OverwritePolicy.RENAME,
    ))

    assert repository.received_output == tmp_path / "ocupado_1.pdf"


def test_cannot_write_over_the_source_document(scenario):
    use_case, _, source, _ = scenario()

    with pytest.raises(InvalidOutputPathException, match="mismo archivo de origen"):
        use_case.execute(SplitPdfRequest(source.storage_path, PageSelection.parse("1-5"), output_path=source.storage_path))


def test_execute_rejects_selection_beyond_document(scenario):
    use_case, repository, source, _ = scenario(page_count=10)

    with pytest.raises(InvalidPageRangeException):
        use_case.execute(SplitPdfRequest(source.storage_path, PageSelection.parse("1-50")))

    assert source.status == PdfProcessingStatus.UPLOADED, "Validar no debe alterar el estado"
    assert repository.received_selection is None


def test_execute_marks_source_as_failed_and_propagates_engine_error(scenario):
    use_case, _, source, _ = scenario(fail_on_split=True)

    with pytest.raises(RuntimeError, match="engine exploded"):
        use_case.execute(SplitPdfRequest(source.storage_path, PageSelection.parse("1-5")))

    assert source.status == PdfProcessingStatus.FAILED


def test_suggest_output_path_does_not_touch_disk(scenario, tmp_path):
    use_case, _, source, _ = scenario()

    suggested = use_case.suggest_output_path(source, PageSelection.parse("1-5,10"))

    assert suggested == source.storage_path.parent / "book_1-5_10.pdf"
    assert not suggested.exists()


def test_suggest_output_path_accepts_a_target_directory(scenario, tmp_path):
    use_case, _, source, _ = scenario()

    suggested = use_case.suggest_output_path(source, PageSelection.parse("3"), directory=tmp_path / "otro")

    assert suggested == tmp_path / "otro" / "book_3.pdf"
