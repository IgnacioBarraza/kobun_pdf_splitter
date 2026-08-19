import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, List, Optional, Sequence

from kobun.application.interfaces.file_storage import FileStorage
from kobun.domain.pdf.exceptions.file_open_exception import FileOpenException
from kobun.domain.pdf.exceptions.invalid_output_path_exception import InvalidOutputPathException

# Tope defensivo para la búsqueda de nombre libre: si hay 999 variantes
# ocupadas, algo está mal en el flujo y es mejor fallar que iterar sin fin.
_MAX_RENAME_ATTEMPTS = 999

WINDOWS = "win32"
MACOS = "darwin"

MACOS_OPENER = "open"
LINUX_OPENER = "xdg-open"


class LocalFileStorage(FileStorage):
    """
    Implementación de FileStorage sobre el sistema de archivos local.

    `platform` y `spawn` se inyectan por el mismo motivo que en
    AppDirectories: permiten verificar el comando de apertura de las tres
    plataformas sin lanzar procesos ni depender del sistema donde corre el test.
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
        Comando que lanza el visor predeterminado en sistemas tipo Unix.

        Windows no usa un comando sino la API del sistema, así que allí este
        método no se invoca.
        """
        opener = MACOS_OPENER if self.is_macos else LINUX_OPENER

        return [opener, str(path)]

    @staticmethod
    def _start_file(path: Path) -> None:
        """
        `os.startfile` sólo existe en Windows, por eso se resuelve en runtime.
        """
        starter = getattr(os, "startfile", None)
        if starter is None:
            raise FileOpenException("Esta plataforma no expone os.startfile.")

        starter(str(path))

    @staticmethod
    def _spawn_detached(command: Sequence[str]) -> None:
        """
        Lanza el visor sin esperarlo: la app no debe quedar bloqueada mientras
        el usuario lee el PDF.

        Sólo detecta fallos inmediatos, como que `xdg-open` no esté instalado.
        Si el lanzador arranca pero después no encuentra visor asociado, eso
        ocurre en otro proceso y ya no es observable desde acá.
        """
        subprocess.Popen(
            list(command),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @staticmethod
    def _normalize(path: Path) -> Path:
        """
        Resuelve la ruta sin exigir que exista, para poder comparar rutas
        relativas ("./book.pdf") con absolutas.
        """
        return Path(os.path.abspath(os.path.normpath(str(path))))
