"""
Catalogue of the themes shipped with the application.
"""
from pathlib import Path
from typing import Tuple

from kobun.shared.config.app_settings import THEMES_DIRECTORY

LIGHT_THEME = "light"
DARK_THEME = "dark"

AVAILABLE_THEMES: Tuple[str, ...] = (
    # Light
    LIGHT_THEME,
    "washi_shu",
    "ai_indigo",
    "matcha",
    "sumi",
    # Dark
    DARK_THEME,
    "yozora",
    "kuro",
    "take",
    "murasaki",
)
"""Themes the user can choose from, in listing order.

Light ones first, dark ones after: the selector groups them by background
luminance rather than by this order, but listing them this way keeps the list
from jumping between groups.

Each JSON declares its own display name in its `label` field."""


def theme_file(name: str) -> Path:
    """
    Path to a shipped theme's JSON.

    :param name: Theme name, without extension.
    """
    return THEMES_DIRECTORY / f"{name}.json"


def is_known_theme(name: str) -> bool:
    return name in AVAILABLE_THEMES
