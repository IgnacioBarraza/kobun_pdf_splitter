from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from kobun.domain.history.exceptions.invalid_export_record_exception import (
    InvalidExportRecordException,
)
from kobun.domain.pdf.value_objects.page_selection import PageSelection


@dataclass(frozen=True, slots=True)
class ExportRecord:
    """
    An export that actually happened.

    Immutable: it describes a past fact, so being able to edit it makes no
    sense. It keeps the selection as a Value Object rather than text so the UI
    can offer "repeat this export" without parsing again.
    """

    source_path: Path
    selection: PageSelection
    output_path: Path
    page_count: int
    size_bytes: int
    created_at: datetime

    title: Optional[str] = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not str(self.source_path):
            raise InvalidExportRecordException("El registro necesita una ruta de origen.")

        if not str(self.output_path):
            raise InvalidExportRecordException("El registro necesita una ruta de destino.")

        if self.page_count <= 0:
            raise InvalidExportRecordException("Una exportación debe tener al menos una página.")

        if self.size_bytes < 0:
            raise InvalidExportRecordException("El tamaño no puede ser negativo.")

        if self.created_at.tzinfo is None:
            raise InvalidExportRecordException("La fecha de creación debe incluir zona horaria.")

    @property
    def source_filename(self) -> str:
        return self.source_path.name

    @property
    def output_filename(self) -> str:
        return self.output_path.name

    def __str__(self) -> str:
        return f"{self.source_filename} [{self.selection}] -> {self.output_filename}"
