from pathlib import Path

from kobun.application.interfaces.file_storage import FileStorage
from kobun.domain.pdf.exceptions.invalid_output_path_exception import InvalidOutputPathException
from kobun.domain.pdf.services.pdf_splitter_service import PDF_SUFFIX
from kobun.domain.pdf.value_objects.overwrite_policy import OverwritePolicy


class OutputPathResolver:
    """
    Convierte lo que el usuario eligió como destino en una ruta de archivo
    concreta y segura para escribir.

    Está separado del use case a propósito: la UI necesita mostrar "se
    guardará en X" *antes* de ejecutar el split, así que resolver la ruta
    tiene que poder invocarse por su cuenta.
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
        :param requested: Lo que eligió el usuario: un archivo .pdf o un
            directorio existente.
        :param source_path: PDF de origen, para no escribir sobre él.
        :param default_filename: Nombre a usar si `requested` es un directorio.
        :param policy: Qué hacer si el archivo de destino ya existe.
        :return: Ruta de archivo lista para escribir.
        :raises InvalidOutputPathException: Si el destino no es utilizable.
        """
        target = self._as_file_path(requested, default_filename)

        self._reject_source_overwrite(target, source_path)
        self._file_storage.ensure_writable_directory(target.parent)

        return self._apply_policy(target, policy)

    def _as_file_path(self, requested: Path, default_filename: str) -> Path:
        """
        Acepta un directorio existente (le agrega el nombre por defecto) o una
        ruta que ya termine en .pdf. Cualquier otra cosa es un error explícito:
        adivinar la intención del usuario aquí produce archivos en lugares
        inesperados.
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
        Escribir el resultado sobre el PDF de origen lo corrompe: el motor lo
        tiene abierto para leer mientras guarda.
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

        # Comparación por valor y no por identidad: OverwritePolicy es un str
        # Enum justamente para tolerar que llegue como texto desde un combo de
        # Qt, un archivo de configuración o la línea de comandos.
        if policy == OverwritePolicy.OVERWRITE:
            return target

        if policy == OverwritePolicy.RENAME:
            return self._file_storage.unique_path(target)

        raise InvalidOutputPathException(
            f"El archivo de salida ya existe: {target}. "
            f"Usá OverwritePolicy.OVERWRITE o RENAME para continuar."
        )
