from datetime import datetime, timezone
from pathlib import Path

from kobun.application.dto.split_pdf_request import SplitPdfRequest
from kobun.application.dto.split_pdf_response import SplitPdfResponse
from kobun.domain.pdf.value_objects.overwrite_policy import OverwritePolicy
from kobun.domain.pdf.value_objects.page_selection import PageSelection


def build_response(**overrides) -> SplitPdfResponse:
    defaults = dict(
        source_path=Path("/libros/book.pdf"),
        selection=PageSelection.parse("1-5,10"),
        output_path=Path("/libros/book_1-5_10.pdf"),
        output_size_bytes=2048,
        page_count=6,
        completed_at=datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc),
        title="Libro (1-5,10)",
    )
    return SplitPdfResponse(**{**defaults, **overrides})


# =========================
# Request
# =========================

def test_request_defaults_to_no_output_and_failing_on_collision():
    request = SplitPdfRequest(Path("book.pdf"), PageSelection.parse("1-5"))

    assert request.output_path is None
    assert request.policy is OverwritePolicy.FAIL


def test_request_normalizes_string_paths():
    """The UI can pass straight through whatever the file dialog returns."""
    request = SplitPdfRequest("book.pdf", PageSelection.parse("1-5"), output_path="salida.pdf")

    assert isinstance(request.input_path, Path)
    assert isinstance(request.output_path, Path)


def test_request_is_immutable():
    request = SplitPdfRequest(Path("book.pdf"), PageSelection.parse("1-5"))

    try:
        request.input_path = Path("otro.pdf")
        assert False, "the request should not be mutable"
    except AttributeError:
        pass


def test_requests_with_the_same_content_are_equal():
    first = SplitPdfRequest(Path("book.pdf"), PageSelection.parse("1-5,3-8"))
    second = SplitPdfRequest(Path("book.pdf"), PageSelection.parse("1-8"))

    assert first == second, "the selection is canonicalised, so both are the same request"


# =========================
# Response
# =========================

def test_response_exposes_filenames_derived_from_paths():
    response = build_response()

    assert response.source_filename == "book.pdf"
    assert response.output_filename == "book_1-5_10.pdf"


def test_response_keeps_the_three_facts_history_needs():
    """Source, selection and destination only coexist here."""
    response = build_response()

    assert response.source_path == Path("/libros/book.pdf")
    assert str(response.selection) == "1-5,10"
    assert response.output_path == Path("/libros/book_1-5_10.pdf")


def test_response_timestamp_is_timezone_aware():
    assert build_response().completed_at.tzinfo is not None


def test_response_reports_the_real_path_when_renamed():
    response = build_response(output_path=Path("/libros/book_1-5_10_1.pdf"))

    assert response.output_filename == "book_1-5_10_1.pdf"


def test_response_string_summarizes_the_operation():
    assert str(build_response()) == "book.pdf [1-5,10] -> book_1-5_10.pdf"


def test_response_is_immutable():
    response = build_response()

    try:
        response.page_count = 99
        assert False, "the response should not be mutable"
    except AttributeError:
        pass


def test_request_accepts_a_policy_given_as_text():
    """OverwritePolicy es str Enum para tolerar valores desde Qt o config."""
    request = SplitPdfRequest(Path("book.pdf"), PageSelection.parse("1-5"), policy="overwrite")

    assert request.policy == OverwritePolicy.OVERWRITE
