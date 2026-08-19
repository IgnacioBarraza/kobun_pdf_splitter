"""
Traducción de excepciones a mensajes para el usuario.

Separa dos cosas que no deben confundirse:

- **Errores esperados**: el usuario pidió algo que no se puede hacer. Se
  muestran tal cual, la aplicación sigue andando.
- **Errores inesperados**: un bug nuestro. Se muestra un texto genérico y el
  detalle queda para el log, porque un traceback en pantalla no le sirve a
  nadie y tragarse la excepción en silencio es peor.

Esta distinción es posible porque el dominio garantiza que sólo deja escapar
sus propias excepciones; cualquier otra cosa es, por definición, un bug.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Type

from kobun.domain.history.exceptions.invalid_export_record_exception import (
    InvalidExportRecordException,
)
from kobun.domain.pdf.exceptions.encrypted_pdf_exception import EncryptedPdfException
from kobun.domain.pdf.exceptions.file_open_exception import FileOpenException
from kobun.domain.pdf.exceptions.invalid_output_path_exception import InvalidOutputPathException
from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException
from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException
from kobun.domain.pdf.exceptions.invalid_pdf_metadata_exception import (
    InvalidPdfMetadataException,
)
from kobun.domain.pdf.exceptions.pdf_not_found_exception import PdfNotFoundException

UNEXPECTED_ERROR_MESSAGE = (
    "Ocurrió un error inesperado. Si vuelve a pasar, reportalo con el detalle técnico."
)

# Errores que el usuario puede provocar y corregir. El orden no importa: la
# búsqueda es por tipo exacto y luego por herencia.
EXPECTED_ERRORS = (
    PdfNotFoundException,
    EncryptedPdfException,
    InvalidPdfException,
    InvalidPdfMetadataException,
    InvalidPageRangeException,
    InvalidOutputPathException,
    FileOpenException,
    InvalidExportRecordException,
)

# Textos que reemplazan al mensaje del dominio cuando la UI quiere otro tono.
# Lo que no esté acá usa el mensaje original, que ya es legible.
_OVERRIDES: Dict[Type[Exception], str] = {
    EncryptedPdfException: (
        "El PDF está protegido con contraseña. Quitale la protección e intentá de nuevo."
    ),
}


def is_expected(error: Exception) -> bool:
    """
    True si el error es parte del uso normal de la aplicación y no un bug.
    """
    return isinstance(error, EXPECTED_ERRORS)


def translate(error: Exception) -> str:
    """
    Mensaje a mostrarle al usuario.

    :param error: Excepción capturada en la capa de presentación.
    """
    if not is_expected(error):
        return UNEXPECTED_ERROR_MESSAGE

    for error_type, message in _OVERRIDES.items():
        if isinstance(error, error_type):
            return message

    return str(error) or UNEXPECTED_ERROR_MESSAGE


def technical_detail(error: Exception) -> str:
    """
    Detalle para el log o para un panel de "ver más". Nunca es el mensaje
    principal.
    """
    return f"{type(error).__name__}: {error}"


EXPECTED_TITLE = "No se pudo completar la operación"
UNEXPECTED_TITLE = "Error inesperado"


@dataclass(frozen=True)
class ErrorPrompt:
    """
    Qué mostrar en un diálogo de error, decidido sin depender de Qt.

    Separar la decisión de la presentación permite testear la política —qué
    título, qué ícono, si se ofrece detalle técnico— sin abrir ventanas.
    """

    title: str
    message: str
    is_critical: bool
    detail: Optional[str] = None


def build_error_prompt(error: Exception) -> ErrorPrompt:
    """
    Traduce una excepción al contenido de su diálogo.

    Los errores esperados son advertencias con el mensaje ya listo. Los
    inesperados son críticos y llevan el detalle técnico aparte, para que el
    usuario pueda copiarlo al reportar sin tener que leerlo.
    """
    expected = is_expected(error)

    return ErrorPrompt(
        title=EXPECTED_TITLE if expected else UNEXPECTED_TITLE,
        message=translate(error),
        is_critical=not expected,
        detail=None if expected else technical_detail(error),
    )
