from datetime import datetime, timezone
from pathlib import Path

import pytest

from kobun.domain.history.entities.export_record import ExportRecord
from kobun.domain.history.exceptions.invalid_export_record_exception import (
    InvalidExportRecordException,
)
from kobun.domain.pdf.value_objects.page_selection import PageSelection

WHEN = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)


def build(**overrides) -> ExportRecord:
    defaults = dict(
        source_path=Path("/libros/book.pdf"),
        selection=PageSelection.parse("1-5,10"),
        output_path=Path("/libros/book_1-5_10.pdf"),
        page_count=6,
        size_bytes=2048,
        created_at=WHEN,
    )
    return ExportRecord(**{**defaults, **overrides})


def test_record_exposes_filenames():
    record = build()

    assert record.source_filename == "book.pdf"
    assert record.output_filename == "book_1-5_10.pdf"


def test_record_keeps_the_selection_as_a_value_object():
    """Keeping the VO allows offering "repeat export" without reparsing."""
    record = build()

    assert record.selection.total_pages == 6
    assert record.selection.max_page == 10


def test_each_record_gets_its_own_id():
    assert build().id != build().id


def test_record_is_immutable():
    record = build()

    with pytest.raises(AttributeError):
        record.page_count = 99


def test_record_string_summarizes_the_export():
    assert str(build()) == "book.pdf [1-5,10] -> book_1-5_10.pdf"


def test_record_requires_pages():
    with pytest.raises(InvalidExportRecordException, match="al menos una página"):
        build(page_count=0)


def test_record_rejects_negative_size():
    with pytest.raises(InvalidExportRecordException, match="no puede ser negativo"):
        build(size_bytes=-1)


def test_record_requires_timezone_aware_date():
    with pytest.raises(InvalidExportRecordException, match="zona horaria"):
        build(created_at=datetime(2026, 8, 5, 12, 0))


def test_record_accepts_zero_size():
    """A PDF of blank pages can be tiny, but never negative."""
    assert build(size_bytes=0).size_bytes == 0
