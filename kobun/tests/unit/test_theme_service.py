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

@pytest.mark.parametrize("name", AVAILABLE_THEMES)
def test_shipped_themes_exist_and_are_loadable(name):
    """Cada paleta del catálogo debe poder cargarse."""
    theme = JsonThemeSource().load(name)

    assert theme.name == name


@pytest.mark.parametrize("name", AVAILABLE_THEMES)
def test_shipped_themes_define_every_token_the_stylesheet_uses(name):
    """
    Regresión: los JSON estuvieron vacíos y la ventana no podía pintarse.
    """
    requeridos = {
        "background", "surface", "surface_alt", "primary", "primary_hover",
        "border", "border_strong", "danger", "success",
    }
    requeridos_texto = {"primary", "secondary", "inverse", "disabled"}

    colores = json.loads(theme_file(name).read_text(encoding="utf-8"))["colors"]

    assert requeridos <= colores.keys(), f"faltan tokens en {name}"
    assert requeridos_texto <= colores["text"].keys(), f"faltan tokens de texto en {name}"


@pytest.mark.parametrize("name", AVAILABLE_THEMES)
def test_every_shipped_theme_declares_a_label(name):
    """El selector muestra `label`; sin él la fila diría "washi_shu"."""
    theme = JsonThemeSource().load(name)

    assert theme.label
    assert theme.display_name == theme.label


def test_display_name_falls_back_to_a_readable_name():
    sin_etiqueta = AppTheme(name="washi_shu", colors={"background": "#ffffff"})

    assert sin_etiqueta.display_name == "Washi Shu"


def test_dark_is_detected_from_the_background_not_the_name():
    """
    Con varias paletas el nombre dejó de ser confiable: una oscura que no se
    llame "dark" recibiría el ícono de flecha equivocado.
    """
    oscura = AppTheme(name="yozora", colors={"background": "#14110f"})
    clara = AppTheme(name="tenebroso", colors={"background": "#faf7f5"})

    assert oscura.is_dark is True
    assert clara.is_dark is False


def test_dark_falls_back_to_the_name_when_the_color_is_unreadable():
    roto = AppTheme(name="dark", colors={"background": "no-es-un-color"})

    assert roto.is_dark is True


def test_the_catalog_has_both_light_and_dark_palettes():
    temas = [JsonThemeSource().load(n) for n in AVAILABLE_THEMES]
    oscuros = [t.name for t in temas if t.is_dark]
    claros = [t.name for t in temas if not t.is_dark]

    assert len(oscuros) >= 2, "hacen falta varias paletas oscuras, no una sola"
    assert len(claros) >= 2
    assert DARK_THEME in oscuros
    assert LIGHT_THEME in claros


def test_light_and_dark_palettes_are_listed_grouped():
    """Los claros van primero: la lista no debe saltar de un grupo a otro."""
    oscuridad = [JsonThemeSource().load(n).is_dark for n in AVAILABLE_THEMES]

    assert oscuridad == sorted(oscuridad), "el catálogo alterna claros y oscuros"


def test_available_lists_the_whole_catalog_in_order():
    service = ThemeService(InMemoryPreferences(), JsonThemeSource())

    assert [t.name for t in service.available()] == list(AVAILABLE_THEMES)


def test_available_skips_themes_that_cannot_be_loaded():
    """Vale más un selector incompleto que una ventana que no abre."""
    source = FakeThemeSource(broken={"matcha", "sumi"})
    service = ThemeService(InMemoryPreferences(), source)

    nombres = [t.name for t in service.available()]

    assert "matcha" not in nombres
    assert LIGHT_THEME in nombres
    assert len(nombres) == len(AVAILABLE_THEMES) - 2


@pytest.mark.parametrize("name", AVAILABLE_THEMES)
def test_any_catalog_theme_can_be_selected_and_persisted(name):
    preferences = InMemoryPreferences()
    service = ThemeService(preferences, JsonThemeSource())

    assert service.select(name).name == name
    assert preferences.preferences.theme_name == name
    assert service.current().name == name


def test_theme_paths_are_package_relative():
    assert theme_file(LIGHT_THEME).is_absolute()
    assert theme_file(LIGHT_THEME).exists()


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


# =========================
# Legibilidad
# =========================

MIN_CONTRAST = 4.5
"""Mínimo de WCAG AA para texto normal."""


def _relative_luminance(hex_color: str) -> float:
    raw = hex_color.lstrip("#")
    canales = [int(raw[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    canales = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]

    return 0.2126 * canales[0] + 0.7152 * canales[1] + 0.0722 * canales[2]


def contrast_ratio(first: str, second: str) -> float:
    """Relación de contraste entre dos colores, de 1 (igual) a 21 (blanco/negro)."""
    primera, segunda = _relative_luminance(first), _relative_luminance(second)

    return (max(primera, segunda) + 0.05) / (min(primera, segunda) + 0.05)


def test_contrast_ratio_matches_known_values():
    """Ancla del cálculo: blanco sobre negro es el máximo posible."""
    assert contrast_ratio("#ffffff", "#000000") == pytest.approx(21.0, abs=0.01)
    assert contrast_ratio("#777777", "#777777") == pytest.approx(1.0, abs=0.01)


@pytest.mark.parametrize("name", AVAILABLE_THEMES)
def test_every_theme_keeps_text_readable(name):
    """
    Ninguna paleta puede entrar con texto ilegible.

    Detectó que el rojo original del tema claro daba 4.44 con el texto blanco
    del botón principal, justo por debajo del mínimo.
    """
    theme = JsonThemeSource().load(name)
    fondo = theme.get_color("background")
    panel = theme.get_color("surface")

    combinaciones = {
        "texto sobre fondo": (theme.get_text_color("primary"), fondo),
        "texto sobre panel": (theme.get_text_color("primary"), panel),
        "texto secundario sobre fondo": (theme.get_text_color("secondary"), fondo),
        "texto del botón sobre el acento": (
            theme.get_text_color("inverse"),
            theme.get_color("primary"),
        ),
    }

    for descripcion, (frente, atras) in combinaciones.items():
        ratio = contrast_ratio(frente, atras)
        assert ratio >= MIN_CONTRAST, f"{name}: {descripcion} da {ratio:.2f}"


@pytest.mark.parametrize("name", AVAILABLE_THEMES)
def test_every_theme_separates_panels_from_the_background(name):
    """
    Si `surface` es casi idéntico al fondo, los paneles desaparecen y todas
    las paletas se ven iguales.
    """
    theme = JsonThemeSource().load(name)

    ratio = contrast_ratio(theme.get_color("surface"), theme.get_color("background"))

    assert ratio >= 1.05, f"{name}: los paneles no se distinguen del fondo ({ratio:.3f})"


def channel_distance(first: str, second: str) -> int:
    """Mayor diferencia entre canales RGB de dos colores, de 0 a 255."""
    return max(
        abs(int(first.lstrip("#")[i:i + 2], 16) - int(second.lstrip("#")[i:i + 2], 16))
        for i in (0, 2, 4)
    )


@pytest.mark.parametrize("dark_group", [False, True], ids=["claros", "oscuros"])
def test_palettes_of_the_same_group_are_visually_distinct(dark_group):
    """
    Lo que motivó rehacer las paletas: washi y light compartían fondo cálido y
    acento rojo, así que cambiar de tema no se notaba.

    Se compara dentro de cada grupo; entre claros y oscuros la diferencia es
    evidente y no hace falta medirla.
    """
    temas = [JsonThemeSource().load(n) for n in AVAILABLE_THEMES]
    grupo = [t for t in temas if t.is_dark is dark_group]
    fondos = {t.name: t.get_color("background") for t in grupo}

    assert len(grupo) >= 2
    assert len(set(fondos.values())) == len(grupo), "hay fondos repetidos"

    for primero in fondos:
        for segundo in fondos:
            if primero >= segundo:
                continue

            distancia = channel_distance(fondos[primero], fondos[segundo])
            assert distancia >= 8, (
                f"{primero} y {segundo} tienen fondos casi idénticos ({distancia})"
            )


def test_the_catalog_is_balanced_between_light_and_dark():
    """
    Mismo número de paletas claras y oscuras: quien trabaja de noche tiene
    tantas opciones como quien trabaja de día.
    """
    temas = [JsonThemeSource().load(n) for n in AVAILABLE_THEMES]
    oscuros = sum(1 for t in temas if t.is_dark)

    assert oscuros == len(temas) - oscuros, f"{oscuros} oscuras contra {len(temas) - oscuros} claras"


def test_every_theme_uses_a_distinct_accent():
    """
    Dos paletas con el mismo acento se confunden aunque el fondo cambie: el
    color del botón principal es lo que más se ve.
    """
    acentos = {n: JsonThemeSource().load(n).get_color("primary") for n in AVAILABLE_THEMES}

    assert len(set(acentos.values())) == len(acentos), f"acentos repetidos en {acentos}"
