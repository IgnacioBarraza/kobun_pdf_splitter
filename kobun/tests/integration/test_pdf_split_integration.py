"""
Tests de integración: ejercitan el use case completo contra PDFs reales
generados en tiempo de test, atravesando repositorio, adapter y PyMuPDF.

Se omiten automáticamente si PyMuPDF no está instalado, para que la suite
unitaria del dominio siga corriendo sin dependencias.
"""
import pytest

pymupdf = pytest.importorskip("pymupdf", reason="PyMuPDF no instalado")

from kobun.application.use_cases.split_pdf_use_case import SplitPdfUseCase
from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService
from kobun.domain.pdf.value_objects.page_range import PageRange
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.infrastructure.pdf_engine.pdf_engine_adapter import PdfEngineAdapter
from kobun.infrastructure.repositories.pdf_repository_impl import PyMuPdfRepository

SOURCE_PAGES = 30


@pytest.fixture
def source_pdf(tmp_path):
    """
    PDF de 30 páginas donde cada página dice "PAGINA n", para poder verificar
    que se extrajeron exactamente las páginas pedidas y no un off-by-one.
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
    return SplitPdfUseCase(repository, PdfSplitterService())


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

    result = use_case.execute(source_pdf, output, PageSelection.parse("1-3,10,20-22"))

    assert read_pages(output) == labels(1, 2, 3, 10, 20, 21, 22)
    assert result.page_count == 7


def test_single_page_selection_is_not_off_by_one(use_case, source_pdf, tmp_path):
    output = tmp_path / "single.pdf"

    use_case.execute(source_pdf, output, PageSelection.parse("17"))

    assert read_pages(output) == labels(17)


def test_overlapping_ranges_produce_no_duplicate_pages(use_case, source_pdf, tmp_path):
    output = tmp_path / "overlap.pdf"

    use_case.execute(source_pdf, output, PageSelection.parse("1-5,3-8"))

    assert read_pages(output) == labels(1, 2, 3, 4, 5, 6, 7, 8)


def test_derived_metadata_is_written_to_the_output_file(use_case, source_pdf, tmp_path):
    output = tmp_path / "meta.pdf"

    use_case.execute(source_pdf, output, PageSelection.parse("1-3,10"))
    metadata = read_metadata(output)

    assert metadata["title"] == "Libro Original (1-3,10)"
    assert metadata["author"] == "Ignacio"
    assert metadata["keywords"] == "derecho"
    assert metadata["creator"] == "Kobun PDF Utility"


def test_selection_beyond_document_fails_with_domain_error(use_case, source_pdf, tmp_path):
    with pytest.raises(InvalidPageRangeException):
        use_case.execute(source_pdf, tmp_path / "nope.pdf", PageSelection.parse("28-40"))


def test_engine_failure_is_not_masked_by_cleanup(source_pdf, tmp_path):
    """
    Regresión: el `finally` del repositorio cerraba un documento que podía no
    existir, lo que reemplazaba el error real por un UnboundLocalError.
    """

    class ExplodingAdapter(PdfEngineAdapter):
        def extract_page_ranges(self, src_doc, ranges):
            raise RuntimeError("fallo simulado del motor")

    use_case = SplitPdfUseCase(PyMuPdfRepository(ExplodingAdapter()), PdfSplitterService())

    with pytest.raises(RuntimeError, match="fallo simulado del motor"):
        use_case.execute(source_pdf, tmp_path / "boom.pdf", PageSelection.parse("1-2"))


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
