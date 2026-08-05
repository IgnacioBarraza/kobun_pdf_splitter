from enum import Enum


class OverwritePolicy(str, Enum):
    """
    Qué hacer cuando el archivo de salida ya existe.

    El default del sistema es FAIL: exportar nunca debe destruir un archivo
    previo sin que alguien lo haya pedido explícitamente.
    """

    FAIL = "fail"
    """Aborta con InvalidOutputPathException."""

    OVERWRITE = "overwrite"
    """Reemplaza el archivo existente."""

    RENAME = "rename"
    """Busca el primer nombre libre: book_1.pdf, book_2.pdf, ..."""
