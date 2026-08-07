import json

import pytest

from kobun.application.interfaces.preferences_repository import (
    AppPreferences,
    PreferencesRepository,
)
from kobun.application.interfaces.theme_source import ThemeSource
from kobun.application.services.theme_service import ThemeService
from kobun.infrastructure.repositories.json_preferences_repository import (
    JsonPreferencesRepository,
)
from kobun.infrastructure.ui.theme_loader import JsonThemeSource
from kobun.shared.config.app_settings import DEFAULT_THEME_NAME
from kobun.shared.config.theme_settings import (
    AVAILABLE_THEMES,
    DARK_THEME,
    LIGHT_THEME,
    is_known_theme,
    opposite_theme,
    theme_file,
)
from kobun.shared.theme import AppTheme


class InMemoryPreferences(PreferencesRepository):
    def __init__(self, preferences: AppPreferences = None):
        self.preferences = preferences or AppPreferences()
        self.saves = 0

    def load(self) -> AppPreferences:
        return self.preferences

    def save(self, preferences: AppPreferences) -> None:
        self.preferences = preferences
        self.saves += 1


class FakeThemeSource(ThemeSource):
    def __init__(self, broken=()):
        self.broken = set(broken)
        self.requested = []

    def load(self, theme_name: str) -> AppTheme:
        self.requested.append(theme_name)

        if theme_name in self.broken:
            raise ValueError(f"tema roto: {theme_name}")

        return AppTheme(name=theme_name, colors={"background": "#000000"})


# =========================
# Catálogo de temas
# =========================

def test_shipped_themes_exist_and_are_loadable():
    source = JsonThemeSource()

    for name in AVAILABLE_THEMES:
        theme = source.load(name)
        assert theme.name == name


def test_shipped_themes_define_every_token_the_stylesheet_uses():
    """
    Regresión: los JSON estuvieron vacíos y la ventana no podía pintarse.
    """
    requeridos = {"background", "surface", "surface_alt", "primary", "primary_hover", "border"}
    requeridos_texto = {"primary", "secondary", "inverse", "disabled"}

    for name in AVAILABLE_THEMES:
        data = json.loads(theme_file(name).read_text(encoding="utf-8"))
        colores = data["colors"]

        assert requeridos <= colores.keys(), f"faltan tokens en {name}"
        assert requeridos_texto <= colores["text"].keys(), f"faltan tokens de texto en {name}"


def test_theme_paths_are_package_relative():
    assert theme_file(LIGHT_THEME).is_absolute()
    assert theme_file(LIGHT_THEME).exists()


def test_opposite_theme_alternates():
    assert opposite_theme(LIGHT_THEME) == DARK_THEME
    assert opposite_theme(DARK_THEME) == LIGHT_THEME


def test_opposite_of_an_unknown_theme_still_does_something():
    assert opposite_theme("neon") in AVAILABLE_THEMES


def test_is_known_theme():
    assert is_known_theme(LIGHT_THEME)
    assert not is_known_theme("neon")


# =========================
# ThemeService
# =========================

def test_current_uses_the_default_on_first_run():
    service = ThemeService(InMemoryPreferences(), FakeThemeSource())

    assert service.current().name == DEFAULT_THEME_NAME


def test_current_uses_the_saved_preference():
    preferences = InMemoryPreferences(AppPreferences(theme_name=DARK_THEME))
    service = ThemeService(preferences, FakeThemeSource())

    assert service.current().name == DARK_THEME


def test_toggle_switches_and_persists():
    preferences = InMemoryPreferences(AppPreferences(theme_name=LIGHT_THEME))
    service = ThemeService(preferences, FakeThemeSource())

    theme = service.toggle()

    assert theme.name == DARK_THEME
    assert preferences.preferences.theme_name == DARK_THEME


def test_toggle_twice_returns_to_the_start():
    service = ThemeService(InMemoryPreferences(), FakeThemeSource())

    primero = service.toggle().name
    segundo = service.toggle().name

    assert primero != segundo
    assert segundo == DEFAULT_THEME_NAME


def test_selecting_an_unknown_theme_falls_back_to_the_default():
    preferences = InMemoryPreferences()
    service = ThemeService(preferences, FakeThemeSource())

    theme = service.select("neon")

    assert theme.name == DEFAULT_THEME_NAME
    assert preferences.preferences.theme_name == DEFAULT_THEME_NAME


def test_a_broken_theme_falls_back_instead_of_crashing():
    """Un JSON roto no puede dejar la ventana sin dibujar."""
    source = FakeThemeSource(broken={DARK_THEME})
    service = ThemeService(InMemoryPreferences(AppPreferences(theme_name=DARK_THEME)), source)

    assert service.current().name == DEFAULT_THEME_NAME


def test_a_broken_default_theme_is_not_hidden():
    """Si ni el tema por defecto carga, es un bug de empaquetado y debe verse."""
    source = FakeThemeSource(broken={DEFAULT_THEME_NAME})
    service = ThemeService(InMemoryPreferences(), source)

    with pytest.raises(ValueError):
        service.current()


# =========================
# Persistencia de preferencias
# =========================

def test_preferences_default_when_the_file_is_missing(tmp_path):
    repositorio = JsonPreferencesRepository(tmp_path / "preferences.json")

    assert repositorio.load().theme_name == DEFAULT_THEME_NAME


def test_preferences_round_trip(tmp_path):
    repositorio = JsonPreferencesRepository(tmp_path / "preferences.json")

    repositorio.save(AppPreferences(theme_name=DARK_THEME))

    assert JsonPreferencesRepository(repositorio.file_path).load().theme_name == DARK_THEME


def test_preferences_create_their_directory(tmp_path):
    repositorio = JsonPreferencesRepository(tmp_path / "config" / "kobun" / "preferences.json")

    repositorio.save(AppPreferences(theme_name=DARK_THEME))

    assert repositorio.file_path.exists()


def test_corrupt_preferences_fall_back_to_defaults(tmp_path):
    repositorio = JsonPreferencesRepository(tmp_path / "preferences.json")
    repositorio.file_path.write_text("no soy json", encoding="utf-8")

    assert repositorio.load().theme_name == DEFAULT_THEME_NAME


def test_unknown_theme_in_the_file_falls_back(tmp_path):
    repositorio = JsonPreferencesRepository(tmp_path / "preferences.json")
    repositorio.file_path.write_text(json.dumps({"theme_name": "neon"}), encoding="utf-8")

    assert repositorio.load().theme_name == DEFAULT_THEME_NAME


def test_preferences_leave_no_temporary_file(tmp_path):
    repositorio = JsonPreferencesRepository(tmp_path / "preferences.json")

    repositorio.save(AppPreferences(theme_name=DARK_THEME))

    assert list(tmp_path.glob("*.tmp")) == []
