from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from uuid import UUID

import pytest

from kobun.application.dto.split_pdf_response import SplitPdfResponse
from kobun.application.interfaces.history_repository import HistoryRepository
from kobun.application.use_cases.list_history_use_case import ListHistoryUseCase
from kobun.application.use_cases.record_split_use_case import RecordSplitUseCase
from kobun.domain.history.entities.export_record import ExportRecord
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.infrastructure.filesystem.local_file_storage import LocalFileStorage

WHEN = datetime(2026, 8, 5, 12, 0, tzinfo=timezone.utc)


class InMemoryHistoryRepository(HistoryRepository):
    def __init__(self, records: List[ExportRecord] = None):
        self.records: List[ExportRecord] = list(records or [])

    def add(self, record: ExportRecord) -> None:
        self.records.insert(0, record)

    def list_recent(self, limit: Optional[int] = None) -> List[ExportRecord]:
        return self.records if limit is None else self.records[:limit]

    def remove(self, record_id: UUID) -> bool:
        restantes = [r for r in self.records if r.id != record_id]
        cambio = len(restantes) != len(self.records)
        self.records = restantes
        return cambio

    def clear(self) -> None:
        self.records = []


def response(**overrides) -> SplitPdfResponse:
    defaults = dict(
        source_path=Path("/libros/book.pdf"),
        selection=PageSelection.parse("1-5,10"),
        output_path=Path("/libros/book_1-5_10.pdf"),
        output_size_bytes=2048,
        page_count=6,
        completed_at=WHEN,
        title="Libro (1-5,10)",
    )
    return SplitPdfResponse(**{**defaults, **overrides})


def record(path: Path, **overrides) -> ExportRecord:
    defaults = dict(
        source_path=Path("/libros/book.pdf"),
        selection=PageSelection.parse("1-5"),
        output_path=path,
        page_count=5,
        size_bytes=1024,
        created_at=WHEN,
    )
    return ExportRecord(**{**defaults, **overrides})


# =========================
# RecordSplitUseCase
# =========================

def test_recording_maps_every_field_of_the_response():
    repository = InMemoryHistoryRepository()
    use_case = RecordSplitUseCase(repository)

    created = use_case.execute(response())

    assert created.source_path == Path("/libros/book.pdf")
    assert created.output_path == Path("/libros/book_1-5_10.pdf")
    assert created.selection == PageSelection.parse("1-5,10")
    assert created.page_count == 6
    assert created.size_bytes == 2048
    assert created.created_at == WHEN
    assert created.title == "Libro (1-5,10)"


def test_recording_stores_the_record():
    repository = InMemoryHistoryRepository()

    created = RecordSplitUseCase(repository).execute(response())

    assert repository.records == [created]


def test_recording_uses_the_completion_time_not_the_current_time():
    """The history must reflect when the split happened, not when it was saved."""
    repository = InMemoryHistoryRepository()

    created = RecordSplitUseCase(repository).execute(response(completed_at=WHEN))

    assert created.created_at == WHEN


def test_each_recording_gets_a_distinct_id():
    repository = InMemoryHistoryRepository()
    use_case = RecordSplitUseCase(repository)

    assert use_case.execute(response()).id != use_case.execute(response()).id


# =========================
# ListHistoryUseCase
# =========================

@pytest.fixture
def listing():
    def _build(records):
        repository = InMemoryHistoryRepository(records)
        return ListHistoryUseCase(repository, LocalFileStorage()), repository

    return _build


def test_listing_marks_existing_files_as_available(listing, tmp_path):
    existing = tmp_path / "existe.pdf"
    existing.write_bytes(b"%PDF")

    use_case, _ = listing([record(existing)])
    entries = use_case.execute()

    assert entries[0].is_available is True


def test_listing_marks_missing_files_as_unavailable(listing, tmp_path):
    use_case, _ = listing([record(tmp_path / "borrado.pdf")])

    entries = use_case.execute()

    assert entries[0].is_available is False


def test_missing_files_are_marked_not_filtered_out(listing, tmp_path):
    """
    Design decision: dropping the entry silently would confuse the user, who
    remembers exporting that file.
    """
    existing = tmp_path / "existe.pdf"
    existing.write_bytes(b"%PDF")

    use_case, _ = listing([record(existing), record(tmp_path / "borrado.pdf")])
    entries = use_case.execute()

    assert len(entries) == 2
    assert [e.is_available for e in entries] == [True, False]


def test_a_directory_at_the_output_path_is_not_available(listing, tmp_path):
    folder = tmp_path / "carpeta.pdf"
    folder.mkdir()

    use_case, _ = listing([record(folder)])

    assert use_case.execute()[0].is_available is False


def test_listing_respects_the_limit(listing, tmp_path):
    use_case, _ = listing([record(tmp_path / f"{i}.pdf") for i in range(5)])

    assert len(use_case.execute(limit=2)) == 2


def test_listing_preserves_repository_order(listing, tmp_path):
    use_case, _ = listing([record(tmp_path / f"{i}.pdf") for i in range(3)])

    entries = use_case.execute()

    assert [e.record.output_filename for e in entries] == ["0.pdf", "1.pdf", "2.pdf"]


def test_empty_history_returns_an_empty_list(listing):
    use_case, _ = listing([])

    assert use_case.execute() == []


def test_entry_string_flags_unavailable_files(listing, tmp_path):
    use_case, _ = listing([record(tmp_path / "borrado.pdf")])

    assert str(use_case.execute()[0]).endswith("(no disponible)")
