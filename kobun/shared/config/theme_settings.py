"""
Catálogo de temas incluidos con la aplicación.
"""
from pathlib import Path
from typing import Tuple

from kobun.shared.config.app_settings import THEMES_DIRECTORY

LIGHT_THEME = "light"
DARK_THEME = "dark"

AVAILABLE_THEMES: Tuple[str, ...] = (
    # Claros
    LIGHT_THEME,
    "washi_shu",
    "ai_indigo",
    "matcha",
    "sumi",
    # Oscuros
    DARK_THEME,
    "yozora",
    "kuro",
    "take",
    "murasaki",
)
"""Temas que el usuario puede elegir, en el orden en que se listan.

Van los claros primero y los oscuros después: el selector los agrupa por
luminancia del fondo, no por este orden, pero listarlos así evita que la lista
salte de un grupo a otro.

El nombre para mostrar lo declara cada JSON en su campo `label`."""


def theme_file(name: str) -> Path:
    """
    Ruta del JSON de un tema incluido.

    :param name: Nombre del tema, sin extensión.
    """
    return THEMES_DIRECTORY / f"{name}.json"


def is_known_theme(name: str) -> bool:
    return name in AVAILABLE_THEMES
