from abc import ABC, abstractmethod
from pathlib import Path


class FileStorage(ABC):
    """
    Contrato de acceso al sistema de archivos, para que las capas de
    aplicación y dominio puedan razonar sobre rutas sin importar `os`.

    Existe para que la política de ruta de salida sea testeable sin tocar
    disco y para poder sustituirla (por ejemplo, por un almacenamiento
    remoto) sin cambiar los use cases.
    """

    @abstractmethod
    def exists(self, path: Path) -> bool:
        pass

    @abstractmethod
    def is_directory(self, path: Path) -> bool:
        pass

    @abstractmethod
    def is_file(self, path: Path) -> bool:
        pass

    @abstractmethod
    def is_same_file(self, first: Path, second: Path) -> bool:
        """
        True si ambas rutas apuntan al mismo archivo, resolviendo rutas
        relativas y enlaces simbólicos.
        """
        pass

    @abstractmethod
    def ensure_writable_directory(self, directory: Path) -> None:
        """
        Verifica que el directorio exista y admita escritura.

        :raises InvalidOutputPathException: Si no existe, no es un directorio
            o no hay permiso de escritura.
        """
        pass

    @abstractmethod
    def unique_path(self, path: Path) -> Path:
        """
        Devuelve la ruta tal cual si está libre, o la primera variante
        numerada disponible: book.pdf -> book_1.pdf -> book_2.pdf.
        """
        pass
