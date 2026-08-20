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
            raise ValueError(f"broken theme: {theme_name}")

        return AppTheme(name=theme_name, colors={"background": "#000000"})


# =========================
# Theme catalogue
# =========================

@pytest.mark.parametrize("name", AVAILABLE_THEMES)
def test_shipped_themes_exist_and_are_loadable(name):
    """Every palette in the catalogue has to be loadable."""
    theme = JsonThemeSource().load(name)

    assert theme.name == name


@pytest.mark.parametrize("name", AVAILABLE_THEMES)
def test_shipped_themes_define_every_token_the_stylesheet_uses(name):
    """
    Regression: the JSONs were once empty and the window could not be painted.
    """
    required = {
        "background", "surface", "surface_alt", "primary", "primary_hover",
        "border", "border_strong", "danger", "success",
    }
    required_text = {"primary", "secondary", "inverse", "disabled"}

    colours = json.loads(theme_file(name).read_text(encoding="utf-8"))["colors"]

    assert required <= colours.keys(), f"missing tokens in {name}"
    assert required_text <= colours["text"].keys(), f"missing text tokens in {name}"


@pytest.mark.parametrize("name", AVAILABLE_THEMES)
def test_every_shipped_theme_declares_a_label(name):
    """The selector shows `label`; without it the row would read "washi_shu"."""
    theme = JsonThemeSource().load(name)

    assert theme.label
    assert theme.display_name == theme.label


def test_display_name_falls_back_to_a_readable_name():
    unlabelled = AppTheme(name="washi_shu", colors={"background": "#ffffff"})

    assert unlabelled.display_name == "Washi Shu"


def test_dark_is_detected_from_the_background_not_the_name():
    """
    With several palettes the name stopped being reliable: a dark one not
    called "dark" would get the wrong chevron icon.
    """
    dark = AppTheme(name="yozora", colors={"background": "#14110f"})
    light = AppTheme(name="tenebroso", colors={"background": "#faf7f5"})

    assert dark.is_dark is True
    assert light.is_dark is False


def test_dark_falls_back_to_the_name_when_the_color_is_unreadable():
    broken = AppTheme(name="dark", colors={"background": "no-es-un-color"})

    assert broken.is_dark is True


def test_the_catalog_has_both_light_and_dark_palettes():
    themes = [JsonThemeSource().load(n) for n in AVAILABLE_THEMES]
    dark = [t.name for t in themes if t.is_dark]
    light = [t.name for t in themes if not t.is_dark]

    assert len(dark) >= 2, "several dark palettes are needed, not just one"
    assert len(light) >= 2
    assert DARK_THEME in dark
    assert LIGHT_THEME in light


def test_light_and_dark_palettes_are_listed_grouped():
    """Light ones first: the list must not jump between groups."""
    darkness = [JsonThemeSource().load(n).is_dark for n in AVAILABLE_THEMES]

    assert darkness == sorted(darkness), "the catalogue alternates light and dark"


def test_available_lists_the_whole_catalog_in_order():
    service = ThemeService(InMemoryPreferences(), JsonThemeSource())

    assert [t.name for t in service.available()] == list(AVAILABLE_THEMES)


def test_available_skips_themes_that_cannot_be_loaded():
    """An incomplete selector beats a window that does not open."""
    source = FakeThemeSource(broken={"matcha", "sumi"})
    service = ThemeService(InMemoryPreferences(), source)

    names = [t.name for t in service.available()]

    assert "matcha" not in names
    assert LIGHT_THEME in names
    assert len(names) == len(AVAILABLE_THEMES) - 2


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
    """A broken JSON cannot be allowed to leave the window undrawn."""
    source = FakeThemeSource(broken={DARK_THEME})
    service = ThemeService(InMemoryPreferences(AppPreferences(theme_name=DARK_THEME)), source)

    assert service.current().name == DEFAULT_THEME_NAME


def test_a_broken_default_theme_is_not_hidden():
    """If even the default theme fails to load, it is a packaging bug and has to show."""
    source = FakeThemeSource(broken={DEFAULT_THEME_NAME})
    service = ThemeService(InMemoryPreferences(), source)

    with pytest.raises(ValueError):
        service.current()


# =========================
# Preferences persistence
# =========================

def test_preferences_default_when_the_file_is_missing(tmp_path):
    repository = JsonPreferencesRepository(tmp_path / "preferences.json")

    assert repository.load().theme_name == DEFAULT_THEME_NAME


def test_preferences_round_trip(tmp_path):
    repository = JsonPreferencesRepository(tmp_path / "preferences.json")

    repository.save(AppPreferences(theme_name=DARK_THEME))

    assert JsonPreferencesRepository(repository.file_path).load().theme_name == DARK_THEME


def test_preferences_create_their_directory(tmp_path):
    repository = JsonPreferencesRepository(tmp_path / "config" / "kobun" / "preferences.json")

    repository.save(AppPreferences(theme_name=DARK_THEME))

    assert repository.file_path.exists()


def test_corrupt_preferences_fall_back_to_defaults(tmp_path):
    repository = JsonPreferencesRepository(tmp_path / "preferences.json")
    repository.file_path.write_text("no soy json", encoding="utf-8")

    assert repository.load().theme_name == DEFAULT_THEME_NAME


def test_unknown_theme_in_the_file_falls_back(tmp_path):
    repository = JsonPreferencesRepository(tmp_path / "preferences.json")
    repository.file_path.write_text(json.dumps({"theme_name": "neon"}), encoding="utf-8")

    assert repository.load().theme_name == DEFAULT_THEME_NAME


def test_preferences_leave_no_temporary_file(tmp_path):
    repository = JsonPreferencesRepository(tmp_path / "preferences.json")

    repository.save(AppPreferences(theme_name=DARK_THEME))

    assert list(tmp_path.glob("*.tmp")) == []


# =========================
# Readability
# =========================

MIN_CONTRAST = 4.5
"""WCAG AA minimum for normal text."""


def _relative_luminance(hex_colour: str) -> float:
    raw = hex_colour.lstrip("#")
    channels = [int(raw[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]

    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(first: str, second: str) -> float:
    """Contrast ratio between two colours, from 1 (identical) to 21 (black/white)."""
    one, two = _relative_luminance(first), _relative_luminance(second)

    return (max(one, two) + 0.05) / (min(one, two) + 0.05)


def test_contrast_ratio_matches_known_values():
    """Anchor for the maths: white on black is the highest possible."""
    assert contrast_ratio("#ffffff", "#000000") == pytest.approx(21.0, abs=0.01)
    assert contrast_ratio("#777777", "#777777") == pytest.approx(1.0, abs=0.01)


@pytest.mark.parametrize("name", AVAILABLE_THEMES)
def test_every_theme_keeps_text_readable(name):
    """
    No palette gets in with illegible text.

    It caught the light theme's original red scoring 4.44 against the primary
    button's white text, just below the minimum.
    """
    theme = JsonThemeSource().load(name)
    background = theme.get_color("background")
    panel = theme.get_color("surface")

    combinations = {
        "text on background": (theme.get_text_color("primary"), background),
        "text on panel": (theme.get_text_color("primary"), panel),
        "secondary text on background": (theme.get_text_color("secondary"), background),
        "button text on the accent": (
            theme.get_text_color("inverse"),
            theme.get_color("primary"),
        ),
    }

    for description, (front, back) in combinations.items():
        ratio = contrast_ratio(front, back)
        assert ratio >= MIN_CONTRAST, f"{name}: {description} scores {ratio:.2f}"


@pytest.mark.parametrize("name", AVAILABLE_THEMES)
def test_every_theme_separates_panels_from_the_background(name):
    """
    If `surface` is nearly identical to the background, the panels disappear
    and every palette looks the same.
    """
    theme = JsonThemeSource().load(name)

    ratio = contrast_ratio(theme.get_color("surface"), theme.get_color("background"))

    assert ratio >= 1.05, f"{name}: panels are indistinguishable from the background ({ratio:.3f})"


def channel_distance(first: str, second: str) -> int:
    """Largest difference between two colours' RGB channels, from 0 to 255."""
    return max(
        abs(int(first.lstrip("#")[i:i + 2], 16) - int(second.lstrip("#")[i:i + 2], 16))
        for i in (0, 2, 4)
    )


@pytest.mark.parametrize("dark_group", [False, True], ids=["light", "dark"])
def test_palettes_of_the_same_group_are_visually_distinct(dark_group):
    """
    What prompted redoing the palettes: washi and light shared a warm
    background and a red accent, so switching theme was not noticeable.

    Compared within each group; between light and dark the difference is obvious
    and needs no measuring.
    """
    themes = [JsonThemeSource().load(n) for n in AVAILABLE_THEMES]
    group = [t for t in themes if t.is_dark is dark_group]
    backgrounds = {t.name: t.get_color("background") for t in group}

    assert len(group) >= 2
    assert len(set(backgrounds.values())) == len(group), "there are repeated backgrounds"

    for one in backgrounds:
        for two in backgrounds:
            if one >= two:
                continue

            distance = channel_distance(backgrounds[one], backgrounds[two])
            assert distance >= 8, (
                f"{one} and {two} have nearly identical backgrounds ({distance})"
            )


def test_the_catalog_is_balanced_between_light_and_dark():
    """
    The same number of light and dark palettes: someone working at night has
    as many options as someone working by day.
    """
    themes = [JsonThemeSource().load(n) for n in AVAILABLE_THEMES]
    dark = sum(1 for t in themes if t.is_dark)

    assert dark == len(themes) - dark, f"{dark} dark against {len(themes) - dark} light"


def test_every_theme_uses_a_distinct_accent():
    """
    Two palettes with the same accent get confused even if the background
    changes: the primary button's colour is the most visible thing there is.
    """
    accents = {n: JsonThemeSource().load(n).get_color("primary") for n in AVAILABLE_THEMES}

    assert len(set(accents.values())) == len(accents), f"repeated accents in {accents}"
