from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from kobun.domain.pdf.value_objects.overwrite_policy import OverwritePolicy
from kobun.domain.pdf.value_objects.page_selection import PageSelection


@dataclass(frozen=True)
class SplitPdfRequest:
    """
    Todo lo que hace falta para pedir un split.

    Existe para que la UI pueda armar la petición en pasos (el usuario elige
    archivo, después rangos, después destino) y entregarla como una sola
    unidad, en vez de que el use case crezca en parámetros sueltos cada vez
    que aparece una opción nueva.
    """

    input_path: Path
    selection: PageSelection

    output_path: Optional[Path] = None
    """Archivo .pdf de destino o directorio existente. Si es None se usa el
    nombre sugerido junto al archivo de origen."""

    policy: OverwritePolicy = OverwritePolicy.FAIL
    """Qué hacer si el destino ya está ocupado."""

    def __post_init__(self) -> None:
        # Normaliza strings a Path para que la UI pueda pasar lo que reciba del
        # diálogo de archivos sin convertir a mano.
        object.__setattr__(self, "input_path", Path(self.input_path))

        if self.output_path is not None:
            object.__setattr__(self, "output_path", Path(self.output_path))
