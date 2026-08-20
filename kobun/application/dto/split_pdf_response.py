from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from kobun.domain.pdf.value_objects.page_selection import PageSelection


@dataclass(frozen=True)
class SplitPdfResponse:
    """
    The full result of a split: what was asked, what was produced, and when.

    It carries the source and the selection alongside the destination because
    the use case is the only place where those three exist together. Without
    it, both the history and the UI would have to reconstruct the operation by
    matching what they sent against what they got back.

    Flat and free of entities on purpose: that way it serialises straight into
    the history without dragging mutable state along.
    """

    source_path: Path
    selection: PageSelection

    output_path: Path
    """The real, final path. It can differ from the requested one if the
    overwrite policy had to look for a free name."""

    output_size_bytes: int
    page_count: int
    completed_at: datetime
    title: Optional[str] = None

    @property
    def source_filename(self) -> str:
        return self.source_path.name

    @property
    def output_filename(self) -> str:
        return self.output_path.name

    def __str__(self) -> str:
        return f"{self.source_filename} [{self.selection}] -> {self.output_filename}"
