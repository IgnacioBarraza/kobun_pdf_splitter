from pathlib import Path

from kobun.application.interfaces.file_storage import FileStorage
from kobun.domain.pdf.exceptions.invalid_output_path_exception import InvalidOutputPathException
from kobun.domain.pdf.services.pdf_splitter_service import PDF_SUFFIX
from kobun.domain.pdf.value_objects.overwrite_policy import OverwritePolicy


class OutputPathResolver:
    """
    Turns whatever the user picked as a destination into a concrete file path
    that is safe to write.

    Separated from the use case on purpose: the UI needs to show "it will be
    saved to X" *before* running the split, so resolving the path has to be
    callable on its own.
    """

    def __init__(self, file_storage: FileStorage):
        self._file_storage = file_storage

    def resolve(
        self,
        requested: Path,
        source_path: Path,
        default_filename: str,
        policy: OverwritePolicy = OverwritePolicy.FAIL,
    ) -> Path:
        """
        :param requested: What the user picked: a .pdf file or an existing
            directory.
        :param source_path: The source PDF, so as not to write over it.
        :param default_filename: Name to use if `requested` is a directory.
        :param policy: What to do if the destination file already exists.
        :return: A file path ready to write to.
        :raises InvalidOutputPathException: If the destination is unusable.
        """
        target = self._as_file_path(requested, default_filename)

        self._reject_source_overwrite(target, source_path)
        self._file_storage.ensure_writable_directory(target.parent)

        return self._apply_policy(target, policy)

    def _as_file_path(self, requested: Path, default_filename: str) -> Path:
        """
        Accepts an existing directory —appending the default name— or a path
        that already ends in .pdf. Anything else is an explicit error: guessing
        the user's intent here produces files in unexpected places.
        """
        if self._file_storage.is_directory(requested):
            return requested / default_filename

        if requested.suffix.lower() == PDF_SUFFIX:
            return requested

        raise InvalidOutputPathException(
            f"La ruta de salida debe ser un directorio existente o terminar en "
            f"'{PDF_SUFFIX}'. Se recibió: {requested}"
        )

    def _reject_source_overwrite(self, target: Path, source_path: Path) -> None:
        """
        Writing the result over the source PDF corrupts it: the engine holds
        it open for reading while it saves.
        """
        if self._file_storage.is_same_file(target, source_path):
            raise InvalidOutputPathException(
                "La ruta de salida no puede ser el mismo archivo de origen: "
                f"{source_path}"
            )

    def _apply_policy(self, target: Path, policy: OverwritePolicy) -> Path:
        if not self._file_storage.exists(target):
            return target

        if self._file_storage.is_directory(target):
            raise InvalidOutputPathException(
                f"Ya existe un directorio con esa ruta: {target}"
            )

        # Compared by value and not by identity: OverwritePolicy is a str Enum
        # precisely so it tolerates arriving as text from a Qt combo box, a
        # configuration file or the command line.
        if policy == OverwritePolicy.OVERWRITE:
            return target

        if policy == OverwritePolicy.RENAME:
            return self._file_storage.unique_path(target)

        raise InvalidOutputPathException(
            f"El archivo de salida ya existe: {target}. "
            f"Usá OverwritePolicy.OVERWRITE o RENAME para continuar."
        )
