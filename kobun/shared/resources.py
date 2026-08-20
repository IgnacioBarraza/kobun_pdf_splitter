"""
Where the data files that travel with the application live.

This exists because `Path(__file__)` is not a reliable way to find them: it
works while the module physically sits next to its data —a source tree or an
unpacked wheel— but there is no guarantee that stays true inside a frozen
executable, where the code can live in a compressed archive and the data is
extracted somewhere else.

And here that failure would not be silent: if the default theme does not load,
`ThemeService` lets the exception through on purpose, because it is a packaging
bug and hiding it would be worse. The app would not open.

Verified with PyInstaller 6.22 in onefile mode: `importlib.resources` resolves
correctly inside the bundle, so no tool-specific branch is needed. The other
strategies stay as a safety net for packagers that behave differently, and only
come into play if the first one does not yield an existing directory.
"""
import sys
from importlib import resources
from pathlib import Path
from typing import Iterator, Optional

PACKAGE = "kobun.shared"
"""The package holding the data directories."""

_PACKAGE_PARTS = PACKAGE.split(".")


def data_root() -> Path:
    """
    The directory where the package's data lives.

    It tries the strategies in order and returns the first one pointing at a
    real directory. Validating instead of choosing blindly keeps every branch
    from being decorative, and lets a packager that puts the data elsewhere
    keep working without touching this code.
    """
    for candidate in _candidates():
        if candidate is not None and candidate.is_dir():
            return candidate

    # If none exists there is a packaging problem. The most likely path is
    # returned so the error message points at something interpretable.
    return _package_relative()


def data_path(*parts: str) -> Path:
    """
    Path to a data file or directory.

    It returns a real filesystem path and not an abstract object, because its
    consumers need one: Qt's QSS only accepts paths in `image: url(...)`, and
    `QIcon.addFile` reads nothing else either.
    """
    return data_root().joinpath(*parts)


def is_frozen() -> bool:
    """
    True if the application is running from a frozen executable.
    """
    return bool(getattr(sys, "frozen", False))


def _candidates() -> Iterator[Optional[Path]]:
    yield _via_importlib()
    yield _frozen_root()
    yield _package_relative()


def _via_importlib() -> Optional[Path]:
    """
    The standard way to locate a package's data, independent of the packaging
    tool.
    """
    try:
        return Path(str(resources.files(PACKAGE)))
    except (ModuleNotFoundError, TypeError, AttributeError, OSError):
        return None


def _frozen_root() -> Optional[Path]:
    """
    The temporary directory PyInstaller extracts data into, preserving the
    package structure.
    """
    base = getattr(sys, "_MEIPASS", None)

    if base is None or not is_frozen():
        return None

    return Path(base).joinpath(*_PACKAGE_PARTS)


def _package_relative() -> Path:
    return Path(__file__).resolve().parent
