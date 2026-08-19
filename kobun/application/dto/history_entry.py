from dataclasses import dataclass

from kobun.domain.history.entities.export_record import ExportRecord


@dataclass(frozen=True)
class HistoryEntry:
    """
    Un registro del historial junto con su disponibilidad actual.

    El `ExportRecord` describe un hecho pasado y no puede saber si el archivo
    sigue existiendo: el usuario pudo moverlo o borrarlo después. Esa
    comprobación se hace al listar, y viaja aparte para que la UI pueda
    mostrar la entrada en gris y deshabilitar "abrir" en vez de ofrecer una
    ruta muerta.
    """

    record: ExportRecord
    is_available: bool

    def __str__(self) -> str:
        estado = "" if self.is_available else " (no disponible)"
        return f"{self.record}{estado}"
