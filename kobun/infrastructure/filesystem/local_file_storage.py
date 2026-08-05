import os
from pathlib import Path

from kobun.application.interfaces.file_storage import FileStorage
from kobun.domain.pdf.exceptions.invalid_output_path_exception import InvalidOutputPathException

# Tope defensivo para la búsqueda de nombre libre: si hay 999 variantes
# ocupadas, algo está mal en el flujo y es mejor fallar que iterar sin fin.
_MAX_RENAME_ATTEMPTS = 999


class LocalFileStorage(FileStorage):
    """
    Implementación de FileStorage sobre el sistema de archivos local.
    """

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

    @staticmethod
    def _normalize(path: Path) -> Path:
        """
        Resuelve la ruta sin exigir que exista, para poder comparar rutas
        relativas ("./book.pdf") con absolutas.
        """
        return Path(os.path.abspath(os.path.normpath(str(path))))
