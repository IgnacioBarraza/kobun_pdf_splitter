"""
Catálogo de temas incluidos con la aplicación.
"""
from pathlib import Path
from typing import Tuple

from kobun.shared.config.app_settings import DEFAULT_THEME_NAME, THEMES_DIRECTORY

LIGHT_THEME = "light"
DARK_THEME = "dark"

AVAILABLE_THEMES: Tuple[str, ...] = (LIGHT_THEME, DARK_THEME)
"""Temas que el usuario puede elegir. El botón de la ventana alterna entre
estos dos."""

PREVIEW_THEMES: Tuple[str, ...] = ("washi_shu", "ai_indigo", "matcha", "sumi")
"""Paletas japonesas incluidas pero todavía no seleccionables.

Se distribuyen para poder compararlas mientras se define la identidad visual.
No están en AVAILABLE_THEMES a propósito: `is_known_theme` las rechaza, así
que ni el toggle ni un preferences.json editado a mano pueden activarlas.

Los tests las validan igual que a las demás; si no, serían archivos que nadie
mira y que se pudren en silencio."""

SHIPPED_THEMES: Tuple[str, ...] = AVAILABLE_THEMES + PREVIEW_THEMES
"""Todos los JSON de tema que viajan con la aplicación."""


def theme_file(name: str) -> Path:
    """
    Ruta del JSON de un tema incluido.

    :param name: Nombre del tema, sin extensión.
    """
    return THEMES_DIRECTORY / f"{name}.json"


def is_known_theme(name: str) -> bool:
    return name in AVAILABLE_THEMES


def opposite_theme(name: str) -> str:
    """
    El otro tema del par claro/oscuro. Un nombre desconocido devuelve el
    contrario del tema por defecto, para que el botón siempre haga algo.
    """
    if name == DARK_THEME:
        return LIGHT_THEME

    if name == LIGHT_THEME:
        return DARK_THEME

    return DARK_THEME if DEFAULT_THEME_NAME == LIGHT_THEME else LIGHT_THEME
