from abc import ABC, abstractmethod
from pathlib import Path


class FileStorage(ABC):
    """
    Filesystem access contract, so the application and domain layers can
    reason about paths without importing `os`.

    It exists to make the output path policy testable without touching disk,
    and to allow substituting it —for a remote storage, say— without changing
    the use cases.
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
        True if both paths point at the same file, resolving relative paths
        and symbolic links.
        """
        pass

    @abstractmethod
    def ensure_writable_directory(self, directory: Path) -> None:
        """
        Checks the directory exists and accepts writes.

        :raises InvalidOutputPathException: If it does not exist, is not a
            directory, or there is no write permission.
        """
        pass

    @abstractmethod
    def unique_path(self, path: Path) -> Path:
        """
        Returns the path as is if free, or the first available numbered
        variant: book.pdf -> book_1.pdf -> book_2.pdf.
        """
        pass

    @abstractmethod
    def open_in_default_app(self, path: Path) -> None:
        """
        Opens the file with the system's default application.

        It does not wait for that application to finish: it only launches it.

        :raises FileOpenException: If the file does not exist or the system
            could not launch it.
        """
        pass
