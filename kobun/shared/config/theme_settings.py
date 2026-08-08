"""
Catálogo de temas incluidos con la aplicación.
"""
from pathlib import Path
from typing import Tuple

from kobun.shared.config.app_settings import THEMES_DIRECTORY

LIGHT_THEME = "light"
DARK_THEME = "dark"

AVAILABLE_THEMES: Tuple[str, ...] = (
    LIGHT_THEME,
    DARK_THEME,
    "washi_shu",
    "ai_indigo",
    "matcha",
    "sumi",
)
"""Temas que el usuario puede elegir desde el selector, en el orden en que se
listan. El nombre para mostrar lo declara cada JSON en su campo `label`."""


def theme_file(name: str) -> Path:
    """
    Ruta del JSON de un tema incluido.

    :param name: Nombre del tema, sin extensión.
    """
    return THEMES_DIRECTORY / f"{name}.json"


def is_known_theme(name: str) -> bool:
    return name in AVAILABLE_THEMES
