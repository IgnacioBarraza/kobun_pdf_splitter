"""
Reading the arguments the desktop launches the application with.

The .desktop entry declares `MimeType=application/pdf` and `Exec=... %f`, so
the system can launch Kobun with a PDF from "Open with". Without interpreting
that argument the window opened empty, and the association was a broken
promise.
"""
from pathlib import Path
from typing import List, Optional, Sequence

PDF_SUFFIX = ".pdf"


def first_pdf_argument(argv: Optional[Sequence[str]]) -> Optional[Path]:
    """
    The first argument that looks like a PDF, or None.

    It filters by extension and nothing else: whether it is readable is
    LoadPdfUseCase's call, the only place that rule lives. As with drag & drop,
    given several files the first one is taken and the rest ignored.

    :param argv: The process's full arguments, argv[0] included.
    """
    for candidate in _candidates(argv):
        if candidate.suffix.lower() == PDF_SUFFIX:
            return candidate

    return None


def _candidates(argv: Optional[Sequence[str]]) -> List[Path]:
    if not argv:
        return []

    paths = []
    for raw in argv[1:]:
        # Qt's own options (-style, --platform, …) and their values are not
        # files; flags are dropped and the extension filter takes care of the
        # rest.
        if raw.startswith("-") or not raw.strip():
            continue

        paths.append(Path(raw))

    return paths
