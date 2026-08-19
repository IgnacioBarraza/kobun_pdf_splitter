from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from kobun.domain.pdf.value_objects.page_selection import PageSelection


@dataclass(frozen=True)
class SplitPdfResponse:
    """
    Resultado completo de un split: qué se pidió, qué se generó y cuándo.

    Incluye el origen y la selección además del destino porque el use case es
    el único punto donde esos tres datos existen juntos. Sin esto, tanto el
    historial como la UI tendrían que recomponer la operación cruzando lo que
    enviaron con lo que recibieron.

    Es plano y sin entidades a propósito: así se serializa directo al
    historial sin arrastrar estado mutable.
    """

    source_path: Path
    selection: PageSelection

    output_path: Path
    """Ruta final y real. Puede diferir de la pedida si la política de
    sobrescritura tuvo que buscar un nombre libre."""

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
