from dataclasses import dataclass

from kobun.domain.history.entities.export_record import ExportRecord


@dataclass(frozen=True)
class HistoryEntry:
    """
    A history record together with its current availability.

    `ExportRecord` describes a past fact and cannot know whether the file still
    exists: the user may have moved or deleted it afterwards. That check runs
    when listing, and travels separately so the UI can grey the entry out and
    disable "open" instead of offering a dead path.
    """

    record: ExportRecord
    is_available: bool

    def __str__(self) -> str:
        state = "" if self.is_available else " (no disponible)"
        return f"{self.record}{state}"
