import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, List, Optional, Sequence

from kobun.application.interfaces.file_storage import FileStorage
from kobun.domain.pdf.exceptions.file_open_exception import FileOpenException
from kobun.domain.pdf.exceptions.invalid_output_path_exception import InvalidOutputPathException

# Defensive cap on the search for a free name: with 999 variants taken,
# something is wrong upstream and failing beats looping forever.
_MAX_RENAME_ATTEMPTS = 999

WINDOWS = "win32"
MACOS = "darwin"

MACOS_OPENER = "open"
LINUX_OPENER = "xdg-open"


class LocalFileStorage(FileStorage):
    """
    FileStorage implementation over the local filesystem.

    `platform` and `spawn` are injected for the same reason as in
    AppDirectories: they allow verifying the open command of all three
    platforms without spawning processes or depending on the system the test
    runs on.
    """

    def __init__(
        self,
        platform: Optional[str] = None,
        spawn: Optional[Callable[[Sequence[str]], None]] = None,
    ):
        self._platform = platform if platform is not None else sys.platform
        self._spawn = spawn if spawn is not None else self._spawn_detached

    @property
    def is_windows(self) -> bool:
        return self._platform.startswith(WINDOWS)

    @property
    def is_macos(self) -> bool:
        return self._platform == MACOS

    def exists(self, path: Path) -> bool:
        return path.exists()

    def is_directory(self, path: Path) -> bool:
        return path.is_dir()

    def is_file(self, path: Path) -> bool:
        return path.is_file()

    def is_same_file(self, first: Path, second: Path) -> bool:
        if first.exists() and second.exists():
            return os.path.samefile(first, second)

        return self._normalize(first) == self._normalize(second)

    def ensure_writable_directory(self, directory: Path) -> None:
        if not directory.exists():
            raise InvalidOutputPathException(f"El directorio de salida no existe: {directory}")

        if not directory.is_dir():
            raise InvalidOutputPathException(f"La ruta de salida no es un directorio: {directory}")

        if not os.access(directory, os.W_OK):
            raise InvalidOutputPathException(f"No hay permiso de escritura en: {directory}")

    def unique_path(self, path: Path) -> Path:
        if not path.exists():
            return path

        for attempt in range(1, _MAX_RENAME_ATTEMPTS + 1):
            candidate = path.with_name(f"{path.stem}_{attempt}{path.suffix}")
            if not candidate.exists():
                return candidate

        raise InvalidOutputPathException(
            f"No se encontró un nombre libre para {path.name} tras {_MAX_RENAME_ATTEMPTS} intentos."
        )

    def open_in_default_app(self, path: Path) -> None:
        if not path.is_file():
            raise FileOpenException(f"El archivo ya no está disponible: {path}")

        try:
            if self.is_windows:
                self._start_file(path)
            else:
                self._spawn(self.open_command(path))
        except FileOpenException:
            raise
        except Exception as e:
            raise FileOpenException(f"No se pudo abrir '{path.name}': {e}") from e

    def open_command(self, path: Path) -> List[str]:
        """
        The command that launches the default viewer on Unix-like systems.

        Windows uses the system API rather than a command, so this method is
        not called there.
        """
        opener = MACOS_OPENER if self.is_macos else LINUX_OPENER

        return [opener, str(path)]

    @staticmethod
    def _start_file(path: Path) -> None:
        """
        `os.startfile` only exists on Windows, hence the runtime lookup.
        """
        starter = getattr(os, "startfile", None)
        if starter is None:
            raise FileOpenException("Esta plataforma no expone os.startfile.")

        starter(str(path))

    @staticmethod
    def _spawn_detached(command: Sequence[str]) -> None:
        """
        Launches the viewer without waiting for it: the app must not sit
        blocked while the user reads the PDF.

        It only catches immediate failures, such as `xdg-open` not being
        installed. If the launcher starts but then finds no associated viewer,
        that happens in another process and is no longer observable from here.
        """
        subprocess.Popen(
            list(command),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @staticmethod
    def _normalize(path: Path) -> Path:
        """
        Resolves the path without requiring it to exist, so relative paths
        ("./book.pdf") can be compared against absolute ones.
        """
        return Path(os.path.abspath(os.path.normpath(str(path))))
