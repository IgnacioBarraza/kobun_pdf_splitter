"""
Ubicación de los archivos de datos que viajan con la aplicación.

Existe porque `Path(__file__)` no es una forma confiable de encontrarlos:
funciona mientras el módulo esté físicamente al lado de sus datos —el árbol de
fuentes o un wheel desempacado—, pero no hay garantía de que eso siga siendo
cierto dentro de un ejecutable empaquetado, donde el código puede vivir en un
archivo comprimido y los datos se extraen a otro lugar.

Y acá ese fallo no sería silencioso: si el tema por defecto no carga,
`ThemeService` deja pasar la excepción a propósito, porque es un bug de
empaquetado y esconderlo sería peor. La app no abriría.

Verificado con PyInstaller 6.22 en modo onefile: `importlib.resources` resuelve
correctamente dentro del bundle, así que no hace falta una rama específica por
herramienta. Las otras estrategias quedan como red de contención para
empaquetadores que se comporten distinto, y sólo entran si la primera no da un
directorio existente.
"""
import sys
from importlib import resources
from pathlib import Path
from typing import Iterator, Optional

PACKAGE = "kobun.shared"
"""Paquete que contiene los directorios de datos."""

_PACKAGE_PARTS = PACKAGE.split(".")


def data_root() -> Path:
    """
    Directorio donde viven los datos del paquete.

    Prueba las estrategias en orden y devuelve la primera que apunte a un
    directorio real. Se valida en vez de elegir a ciegas: así ninguna rama es
    decorativa y un empaquetador que ubique los datos en otro lado sigue
    funcionando sin tocar este código.
    """
    for candidate in _candidates():
        if candidate is not None and candidate.is_dir():
            return candidate

    # Si ninguna existe hay un problema de empaquetado. Se devuelve la ruta más
    # probable para que el mensaje de error apunte a algo interpretable.
    return _package_relative()


def data_path(*parts: str) -> Path:
    """
    Ruta a un archivo o directorio de datos.

    Devuelve una ruta real del sistema de archivos y no un objeto abstracto,
    porque quienes la consumen lo necesitan así: el QSS de Qt sólo acepta rutas
    en `image: url(...)`, y `QIcon.addFile` tampoco lee de otra cosa.
    """
    return data_root().joinpath(*parts)


def is_frozen() -> bool:
    """
    True si la aplicación corre desde un ejecutable empaquetado.
    """
    return bool(getattr(sys, "frozen", False))


def _candidates() -> Iterator[Optional[Path]]:
    yield _via_importlib()
    yield _frozen_root()
    yield _package_relative()


def _via_importlib() -> Optional[Path]:
    """
    La forma estándar de ubicar datos de un paquete, independiente de la
    herramienta de empaquetado.
    """
    try:
        return Path(str(resources.files(PACKAGE)))
    except (ModuleNotFoundError, TypeError, AttributeError, OSError):
        return None


def _frozen_root() -> Optional[Path]:
    """
    Directorio temporal donde PyInstaller extrae los datos, conservando la
    estructura de paquetes.
    """
    base = getattr(sys, "_MEIPASS", None)

    if base is None or not is_frozen():
        return None

    return Path(base).joinpath(*_PACKAGE_PARTS)


def _package_relative() -> Path:
    return Path(__file__).resolve().parent
