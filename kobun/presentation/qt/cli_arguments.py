"""
Lectura de los argumentos con los que el escritorio lanza la aplicación.

La entrada .desktop declara `MimeType=application/pdf` y `Exec=... %f`, así que
el sistema puede lanzar Kobun con un PDF desde "Abrir con". Sin interpretar ese
argumento, la ventana abría vacía y la asociación era una promesa incumplida.
"""
from pathlib import Path
from typing import List, Optional, Sequence

PDF_SUFFIX = ".pdf"


def first_pdf_argument(argv: Optional[Sequence[str]]) -> Optional[Path]:
    """
    Primer argumento que parece un PDF, o None.

    Se filtra por extensión y nada más: que sea legible lo decide
    LoadPdfUseCase, que es el único lugar donde vive esa regla. Igual que en el
    drag & drop, con varios archivos se toma el primero y se ignora el resto.

    :param argv: Argumentos completos del proceso, incluido argv[0].
    """
    for candidate in _candidates(argv):
        if candidate.suffix.lower() == PDF_SUFFIX:
            return candidate

    return None


def _candidates(argv: Optional[Sequence[str]]) -> List[Path]:
    if not argv:
        return []

    rutas = []
    for raw in argv[1:]:
        # Las opciones de Qt (-style, --platform, …) y sus valores no son
        # archivos; se descartan las banderas y se deja que el filtro por
        # extensión se ocupe del resto.
        if raw.startswith("-") or not raw.strip():
            continue

        rutas.append(Path(raw))

    return rutas
