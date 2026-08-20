from pathlib import Path

import pytest

from kobun.infrastructure.config.infrastructure_settings import AppDirectories
from kobun.shared.config.app_settings import (
    APP_NAME,
    APP_SLUG,
    HISTORY_FILENAME,
    THEMES_DIRECTORY,
)

HOME = Path("/home/tester")


def build(platform: str, environ: dict = None, home: Path = HOME) -> AppDirectories:
    return AppDirectories(platform=platform, environ=environ or {}, home=home)


# =========================
# Linux / XDG
# =========================

def test_linux_defaults_follow_xdg_conventions():
    dirs = build("linux")

    assert dirs.config_dir == HOME / ".config" / APP_SLUG
    assert dirs.data_dir == HOME / ".local" / "share" / APP_SLUG


def test_linux_respects_xdg_environment_variables():
    dirs = build("linux", {
        "XDG_CONFIG_HOME": "/custom/config",
        "XDG_DATA_HOME": "/custom/data",
    })

    assert dirs.config_dir == Path("/custom/config") / APP_SLUG
    assert dirs.data_dir == Path("/custom/data") / APP_SLUG


def test_linux_ignores_relative_xdg_values():
    """The XDG specification requires discarding values that are not absolute."""
    dirs = build("linux", {"XDG_CONFIG_HOME": "relativo/config"})

    assert dirs.config_dir == HOME / ".config" / APP_SLUG


def test_linux_ignores_empty_xdg_values():
    dirs = build("linux", {"XDG_DATA_HOME": ""})

    assert dirs.data_dir == HOME / ".local" / "share" / APP_SLUG


def test_linux_separates_config_from_data():
    dirs = build("linux")

    assert dirs.config_dir != dirs.data_dir


# =========================
# Windows
# =========================

def test_windows_uses_appdata():
    dirs = build("win32", {"APPDATA": r"C:\Users\Tester\AppData\Roaming"})

    esperado = Path(r"C:\Users\Tester\AppData\Roaming") / APP_NAME
    assert dirs.config_dir == esperado
    assert dirs.data_dir == esperado


def test_windows_falls_back_when_appdata_is_missing():
    dirs = build("win32")

    assert dirs.config_dir == HOME / "AppData" / "Roaming" / APP_NAME


def test_windows_uses_the_capitalized_app_name():
    dirs = build("win32", {"APPDATA": "/appdata"})

    assert dirs.config_dir.name == APP_NAME
    assert dirs.config_dir.name != APP_SLUG


# =========================
# macOS
# =========================

def test_macos_uses_application_support():
    dirs = build("darwin")

    esperado = HOME / "Library" / "Application Support" / APP_NAME
    assert dirs.config_dir == esperado
    assert dirs.data_dir == esperado


def test_macos_ignores_xdg_variables():
    dirs = build("darwin", {"XDG_CONFIG_HOME": "/custom"})

    assert dirs.config_dir == HOME / "Library" / "Application Support" / APP_NAME


# =========================
# Shared behaviour
# =========================

def test_file_helpers_join_the_right_directory():
    dirs = build("linux")

    assert dirs.data_file(HISTORY_FILENAME) == dirs.data_dir / HISTORY_FILENAME
    assert dirs.config_file("preferences.json") == dirs.config_dir / "preferences.json"


def test_reading_a_directory_property_does_not_touch_disk(tmp_path):
    dirs = build("linux", home=tmp_path)

    path = dirs.data_dir

    assert not path.exists(), "Consultar la ruta no debe crear nada"


def test_ensure_creates_the_directory_tree(tmp_path):
    dirs = build("linux", home=tmp_path)

    created = dirs.ensure_data_dir()

    assert created.is_dir()
    assert created == dirs.data_dir


def test_ensure_is_idempotent(tmp_path):
    dirs = build("linux", home=tmp_path)

    assert dirs.ensure_config_dir() == dirs.ensure_config_dir()


def test_platform_defaults_to_the_running_system():
    """With no explicit injection it must resolve to something usable."""
    dirs = AppDirectories()

    assert dirs.data_dir.is_absolute()
    assert dirs.data_dir.name in (APP_NAME, APP_SLUG)


# =========================
# Constantes compartidas
# =========================

def test_themes_directory_is_package_relative_and_exists():
    """
    Regression: the window looked for themes in Path("themes"), relative to the
    working directory, so launching the app from another folder failed.
    """
    assert THEMES_DIRECTORY.is_absolute()
    assert THEMES_DIRECTORY.is_dir()
    assert (THEMES_DIRECTORY / "light.json").exists()
    assert (THEMES_DIRECTORY / "dark.json").exists()
