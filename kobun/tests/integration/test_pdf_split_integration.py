"""
Integration tests: they exercise the whole use case against real PDFs generated
at test time, going through repository, adapter and PyMuPDF.

They skip themselves if PyMuPDF is not installed, so the domain's unit suite
keeps running with no dependencies.
"""
import pytest

pymupdf = pytest.importorskip("pymupdf", reason="PyMuPDF is not installed")

from kobun.application.dto.split_pdf_request import SplitPdfRequest
from kobun.application.services.output_path_resolver import OutputPathResolver
from kobun.application.use_cases.list_history_use_case import ListHistoryUseCase
from kobun.application.use_cases.load_pdf_use_case import LoadPdfUseCase
from kobun.application.use_cases.record_split_use_case import RecordSplitUseCase
from kobun.application.use_cases.split_pdf_use_case import SplitPdfUseCase
from kobun.domain.pdf.exceptions.encrypted_pdf_exception import EncryptedPdfException
from kobun.domain.pdf.exceptions.invalid_output_path_exception import InvalidOutputPathException
from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException
from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException
from kobun.domain.pdf.exceptions.pdf_not_found_exception import PdfNotFoundException
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService
from kobun.domain.pdf.value_objects.overwrite_policy import OverwritePolicy
from kobun.domain.pdf.value_objects.page_range import PageRange
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.infrastructure.filesystem.local_file_storage import LocalFileStorage
from kobun.infrastructure.pdf_engine.pdf_engine_adapter import PdfEngineAdapter
from kobun.infrastructure.repositories.json_history_repository import JsonHistoryRepository
from kobun.infrastructure.repositories.pdf_repository_impl import PyMuPdfRepository

SOURCE_PAGES = 30


@pytest.fixture
def source_pdf(tmp_path):
    """
    A 30 page PDF where each page reads "PAGINA n", so it can be verified that
    exactly the requested pages came out and not an off-by-one.
    """
    path = tmp_path / "source.pdf"

    doc = pymupdf.open()
    for number in range(1, SOURCE_PAGES + 1):
        page = doc.new_page()
        page.insert_text((72, 144), f"PAGINA {number}", fontsize=48)
    doc.set_metadata({
        "title": "Libro Original",
        "author": "Ignacio",
        "keywords": "derecho",
    })
    doc.save(path)
    doc.close()

    return path


@pytest.fixture
def repository():
    return PyMuPdfRepository(PdfEngineAdapter())


@pytest.fixture
def use_case(repository):
    return SplitPdfUseCase(
        repository,
        PdfSplitterService(),
        OutputPathResolver(LocalFileStorage()),
    )


@pytest.fixture
def load_use_case(repository):
    return LoadPdfUseCase(repository, PdfSplitterService())


def read_pages(path):
    doc = pymupdf.open(path)
    try:
        return [doc.load_page(i).get_text("text").strip() for i in range(doc.page_count)]
    finally:
        doc.close()


def read_metadata(path):
    doc = pymupdf.open(path)
    try:
        return dict(doc.metadata)
    finally:
        doc.close()


def labels(*numbers):
    return [f"PAGINA {n}" for n in numbers]


def test_discontinuous_selection_extracts_exact_pages(use_case, source_pdf, tmp_path):
    output = tmp_path / "multi.pdf"

    result = use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("1-3,10,20-22"), output))

    assert read_pages(output) == labels(1, 2, 3, 10, 20, 21, 22)
    assert result.page_count == 7


def test_single_page_selection_is_not_off_by_one(use_case, source_pdf, tmp_path):
    output = tmp_path / "single.pdf"

    use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("17"), output))

    assert read_pages(output) == labels(17)


def test_overlapping_ranges_produce_no_duplicate_pages(use_case, source_pdf, tmp_path):
    output = tmp_path / "overlap.pdf"

    use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("1-5,3-8"), output))

    assert read_pages(output) == labels(1, 2, 3, 4, 5, 6, 7, 8)


def test_derived_metadata_is_written_to_the_output_file(use_case, source_pdf, tmp_path):
    output = tmp_path / "meta.pdf"

    use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("1-3,10"), output))
    metadata = read_metadata(output)

    assert metadata["title"] == "Libro Original (1-3,10)"
    assert metadata["author"] == "Ignacio"
    assert metadata["keywords"] == "derecho"
    assert metadata["creator"] == "Kobun PDF Utility"


def test_a_source_without_title_yields_a_clean_derived_title(use_case, tmp_path):
    """
    A real case: a PDF with no title metadata left the exported file with a
    title like "contrato.pdf (3-6)".
    """
    untitled = tmp_path / "2026.03.01_Contrato_Indefinido.pdf"
    doc = pymupdf.open()
    for _ in range(8):
        doc.new_page()
    doc.save(untitled)
    doc.close()

    result = use_case.execute(SplitPdfRequest(untitled, PageSelection.parse("3-6")))
    metadata = read_metadata(result.output_path)

    assert metadata["title"] == "2026.03.01_Contrato_Indefinido (3-6)"
    assert ".pdf" not in metadata["title"]


def test_open_document_derives_a_title_without_the_extension(repository, tmp_path):
    untitled = tmp_path / "apunte.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(untitled)
    doc.close()

    document = repository.open_document(untitled)

    assert document.metadata.title == "apunte"
    assert document.filename == "apunte.pdf", "the filename does keep its extension"


def test_selection_beyond_document_fails_with_domain_error(use_case, source_pdf, tmp_path):
    with pytest.raises(InvalidPageRangeException):
        use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("28-40"), tmp_path / "nope.pdf"))


def test_engine_failure_is_not_masked_by_cleanup(source_pdf, tmp_path):
    """
    Regression: the repository's `finally` closed a document that might not
    exist, which replaced the real error with an UnboundLocalError.
    """

    class ExplodingAdapter(PdfEngineAdapter):
        def extract_page_ranges(self, src_doc, ranges):
            raise RuntimeError("simulated engine failure")

    use_case = SplitPdfUseCase(
        PyMuPdfRepository(ExplodingAdapter()),
        PdfSplitterService(),
        OutputPathResolver(LocalFileStorage()),
    )

    with pytest.raises(RuntimeError, match="simulated engine failure"):
        use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("1-2"), tmp_path / "boom.pdf"))


def test_extract_text_is_one_based(repository, source_pdf):
    document = repository.open_document(source_pdf)

    assert repository.extract_text(document, 1).strip() == "PAGINA 1"
    assert repository.extract_text(document, SOURCE_PAGES).strip() == f"PAGINA {SOURCE_PAGES}"


def test_open_document_reads_source_metadata(repository, source_pdf):
    document = repository.open_document(source_pdf)

    assert document.page_count == SOURCE_PAGES
    assert document.metadata.title == "Libro Original"
    assert document.metadata.author == "Ignacio"
    assert document.metadata.keywords == "derecho"


def test_split_page_range_and_single_page_still_work(repository, source_pdf, tmp_path):
    document = repository.open_document(source_pdf)

    ranged = repository.split_page_range(document, tmp_path / "r.pdf", PageRange(start=4, end=6))
    single = repository.split_single_page(document, tmp_path / "s.pdf", 9)

    assert read_pages(ranged.storage_path) == labels(4, 5, 6)
    assert read_pages(single.storage_path) == labels(9)


def test_merge_pdfs_concatenates_documents(repository, source_pdf, tmp_path):
    document = repository.open_document(source_pdf)
    first = repository.split_page_range(document, tmp_path / "a.pdf", PageRange(start=1, end=2))
    second = repository.split_page_range(document, tmp_path / "b.pdf", PageRange(start=5, end=6))

    merged = repository.merge_pdfs(first, second, tmp_path / "merged.pdf")

    assert read_pages(merged.storage_path) == labels(1, 2, 5, 6)


def test_extract_pages_respects_requested_order(repository, source_pdf, tmp_path):
    document = repository.open_document(source_pdf)

    result = repository.extract_pages(document, [9, 3, 1], tmp_path / "ordered.pdf")

    assert read_pages(result.storage_path) == labels(9, 3, 1)


# =========================================================
# Blindaje de carga (bloque 1)
# =========================================================

def test_load_returns_an_inspectable_document(load_use_case, source_pdf):
    document = load_use_case.execute(source_pdf)

    assert document.page_count == SOURCE_PAGES
    assert document.filename == "source.pdf"
    assert document.metadata.title == "Libro Original"
    assert document.size_bytes > 0
    assert len(document.checksum) == 64


def test_load_accepts_uppercase_pdf_extension(load_use_case, source_pdf, tmp_path):
    upper = tmp_path / "LIBRO.PDF"
    upper.write_bytes(source_pdf.read_bytes())

    assert load_use_case.execute(upper).page_count == SOURCE_PAGES


def test_load_rejects_missing_file(load_use_case, tmp_path):
    with pytest.raises(PdfNotFoundException, match="No se encuentra"):
        load_use_case.execute(tmp_path / "fantasma.pdf")


def test_load_rejects_a_directory(load_use_case, tmp_path):
    """Un drag & drop puede soltar una carpeta."""
    folder = tmp_path / "carpeta.pdf"
    folder.mkdir()

    with pytest.raises(InvalidPdfException, match="no es un archivo"):
        load_use_case.execute(folder)


def test_load_rejects_a_non_pdf_extension(load_use_case, tmp_path):
    text = tmp_path / "notas.txt"
    text.write_text("hola")

    with pytest.raises(InvalidPdfException, match="no es un PDF"):
        load_use_case.execute(text)


def test_load_rejects_an_empty_file(load_use_case, tmp_path):
    empty_file = tmp_path / "empty_file.pdf"
    empty_file.touch()

    with pytest.raises(InvalidPdfException, match="está vacío"):
        load_use_case.execute(empty_file)


def test_load_rejects_a_jpeg_renamed_as_pdf(load_use_case, tmp_path):
    """
    PyMuPDF sniffs the content and opens the JPEG without complaining, so the
    extension filter is not enough: the `is_pdf` check is what stops it.
    """
    disguised = tmp_path / "image.pdf"
    disguised.write_bytes(b"\xff\xd8\xff\xe0JFIF y garbage binaria que no es un PDF")

    with pytest.raises(InvalidPdfException, match="no es un PDF"):
        load_use_case.execute(disguised)


def test_load_rejects_a_truncated_pdf(load_use_case, tmp_path):
    """
    PyMuPDF is very tolerant: instead of failing, it recovers the file and
    reports it as a 0 page PDF. The page count check is what stops it.
    """
    corrupt = tmp_path / "corrupt.pdf"
    corrupt.write_bytes(b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog\ntruncado sin trailer")

    with pytest.raises(InvalidPdfException, match="no contiene páginas"):
        load_use_case.execute(corrupt)


def test_engine_open_errors_are_translated_to_domain_exceptions(source_pdf):
    """
    When the engine does raise on open, the error must not escape as a PyMuPDF
    exception: the UI should only ever have to catch InvalidPdfException.
    """

    class FailingAdapter(PdfEngineAdapter):
        def open_document(self, file_path):
            raise RuntimeError("mupdf: cannot recognize file format")

    use_case = LoadPdfUseCase(PyMuPdfRepository(FailingAdapter()), PdfSplitterService())

    with pytest.raises(InvalidPdfException, match="corrupto o no es un PDF") as error:
        use_case.execute(source_pdf)

    assert isinstance(error.value.__cause__, RuntimeError), "Se conserva la causa original"


def test_load_rejects_a_password_protected_pdf(load_use_case, tmp_path):
    protected = tmp_path / "protected.pdf"

    doc = pymupdf.open()
    doc.new_page()
    doc.save(
        protected,
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        owner_pw="dueno",
        user_pw="secreto",
    )
    doc.close()

    with pytest.raises(EncryptedPdfException, match="protegido con contraseña"):
        load_use_case.execute(protected)


def test_load_rejects_a_non_pdf_format_that_pymupdf_can_open(load_use_case, tmp_path):
    """
    PyMuPDF opens images without trouble. With a .pdf extension it passes the
    extension filter and opens fine, so `is_pdf` has to be asked.
    """
    image = tmp_path / "image_real.pdf"

    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "x")
    pix = page.get_pixmap()
    doc.close()
    pix.save(image, output="png")

    with pytest.raises(InvalidPdfException, match="no es un PDF"):
        load_use_case.execute(image)


def test_engine_exceptions_never_reach_the_caller(load_use_case, tmp_path):
    """
    Todo fallo de carga debe ser capturable con un solo except del dominio.
    """
    casos = [tmp_path / "no_existe.pdf"]

    empty_file = tmp_path / "v.pdf"
    empty_file.touch()
    casos.append(empty_file)

    garbage = tmp_path / "b.pdf"
    garbage.write_bytes(b"no soy un pdf")
    casos.append(garbage)

    for caso in casos:
        with pytest.raises(InvalidPdfException):
            load_use_case.execute(caso)


# =========================================================
# Output path policy
# =========================================================

def test_default_output_lands_next_to_the_source_with_suggested_name(use_case, source_pdf):
    result = use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("1-3,10")))

    assert result.output_path == source_pdf.parent / "source_1-3_10.pdf"
    assert read_pages(result.output_path) == labels(1, 2, 3, 10)


def test_output_directory_receives_the_suggested_name(use_case, source_pdf, tmp_path):
    destination = tmp_path / "exports"
    destination.mkdir()

    result = use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("5-6"), destination))

    assert result.output_path == destination / "source_5-6.pdf"
    assert read_pages(result.output_path) == labels(5, 6)


def test_existing_output_is_not_overwritten_by_default(use_case, source_pdf, tmp_path):
    taken = tmp_path / "ocupado.pdf"
    taken.write_bytes(b"contenido previo")

    with pytest.raises(InvalidOutputPathException, match="ya existe"):
        use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("1-2"), taken))

    assert taken.read_bytes() == b"contenido previo", "El archivo previo debe quedar intacto"


def test_overwrite_policy_replaces_the_existing_file(use_case, source_pdf, tmp_path):
    taken = tmp_path / "ocupado.pdf"
    taken.write_bytes(b"contenido previo")

    result = use_case.execute(SplitPdfRequest(
        source_pdf, PageSelection.parse("1-2"), taken, OverwritePolicy.OVERWRITE
    ))

    assert result.output_path == taken
    assert read_pages(taken) == labels(1, 2)


def test_rename_policy_writes_beside_the_existing_file(use_case, source_pdf, tmp_path):
    taken = tmp_path / "ocupado.pdf"
    taken.write_bytes(b"contenido previo")

    result = use_case.execute(SplitPdfRequest(
        source_pdf, PageSelection.parse("1-2"), taken, OverwritePolicy.RENAME
    ))

    assert result.output_path == tmp_path / "ocupado_1.pdf"
    assert taken.read_bytes() == b"contenido previo"
    assert read_pages(result.output_path) == labels(1, 2)


def test_repeated_exports_with_rename_never_collide(use_case, source_pdf, tmp_path):
    destination = tmp_path / "cap.pdf"

    paths = [
        use_case.execute(SplitPdfRequest(
            source_pdf, PageSelection.parse("1-2"), destination, OverwritePolicy.RENAME
        )).output_path
        for _ in range(3)
    ]

    assert paths == [tmp_path / "cap.pdf", tmp_path / "cap_1.pdf", tmp_path / "cap_2.pdf"]
    assert all(read_pages(path) == labels(1, 2) for path in paths)


def test_cannot_write_the_result_over_the_source_pdf(use_case, source_pdf):
    original = source_pdf.read_bytes()

    with pytest.raises(InvalidOutputPathException, match="mismo archivo de origen"):
        use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("1-2"), source_pdf))

    assert source_pdf.read_bytes() == original, "the source PDF must not be touched"


def test_missing_output_directory_fails_before_processing(use_case, source_pdf, tmp_path):
    with pytest.raises(InvalidOutputPathException, match="no existe"):
        use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("1-2"), tmp_path / "nada" / "x.pdf"))


def test_suggested_path_matches_what_execute_actually_writes(use_case, load_use_case, source_pdf):
    document = load_use_case.execute(source_pdf)
    selection = PageSelection.parse("4-8,20")

    suggested = use_case.suggest_output_path(document, selection)
    result = use_case.execute(SplitPdfRequest(source_pdf, selection))

    assert result.output_path == suggested


# =========================================================
# Historial sobre exportaciones reales
# =========================================================

@pytest.fixture
def history(tmp_path):
    repository = JsonHistoryRepository(tmp_path / "datos" / "history.json")
    almacenamiento = LocalFileStorage()

    return (
        RecordSplitUseCase(repository),
        ListHistoryUseCase(repository, almacenamiento),
        repository,
    )


def test_a_real_export_can_be_recorded_and_listed(use_case, source_pdf, history):
    record_use_case, listing, _ = history

    response = use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("1-3,10")))
    record_use_case.execute(response)

    entries = listing.execute()

    assert len(entries) == 1
    assert entries[0].is_available is True
    assert entries[0].record.output_path == response.output_path
    assert entries[0].record.page_count == 4
    assert entries[0].record.size_bytes == response.output_path.stat().st_size


def test_history_survives_a_new_repository_instance(use_case, source_pdf, history, tmp_path):
    """The history has to survive closing the application."""
    record_use_case, _, repository = history

    record_use_case.execute(use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("2-4"))))

    another_session = ListHistoryUseCase(
        JsonHistoryRepository(repository.file_path), LocalFileStorage()
    )

    assert len(another_session.execute()) == 1


def test_deleted_exports_are_marked_not_removed(use_case, source_pdf, history):
    record_use_case, listing, _ = history

    borrado = use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("1-2")))
    vigente = use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("5-6")))
    record_use_case.execute(borrado)
    record_use_case.execute(vigente)

    borrado.output_path.unlink()
    entries = listing.execute()

    assert len(entries) == 2, "the dead entry is flagged, not filtered out"
    assert entries[0].record.output_path == vigente.output_path
    assert entries[0].is_available is True
    assert entries[1].is_available is False


def test_recorded_selection_can_be_replayed(use_case, source_pdf, history, tmp_path):
    """
    The history keeps the selection as a Value Object, so repeating an export
    does not require parsing text again.
    """
    record_use_case, listing, _ = history
    record_use_case.execute(use_case.execute(SplitPdfRequest(source_pdf, PageSelection.parse("3-5,20"))))

    saved = listing.execute()[0].record.selection
    repeated = use_case.execute(SplitPdfRequest(source_pdf, saved, tmp_path / "repeated.pdf"))

    assert read_pages(repeated.output_path) == labels(3, 4, 5, 20)
