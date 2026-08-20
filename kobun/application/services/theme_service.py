from typing import List

from kobun.application.interfaces.preferences_repository import PreferencesRepository
from kobun.application.interfaces.theme_source import ThemeSource
from kobun.shared.config.app_settings import DEFAULT_THEME_NAME
from kobun.shared.config.theme_settings import AVAILABLE_THEMES, is_known_theme
from kobun.shared.theme import AppTheme


class ThemeService:
    """
    Resolves which theme to show, offers the catalogue and remembers the
    choice.

    Loading a theme never fails outwards as long as the default theme stays
    readable: a broken JSON or an unknown name fall back to it. A mistyped
    colour cannot be allowed to leave the window undrawn.
    """

    def __init__(self, preferences_repository: PreferencesRepository, theme_source: ThemeSource):
        self._preferences_repository = preferences_repository
        self._theme_source = theme_source

    def available(self) -> List[AppTheme]:
        """
        Themes offered to the user, in catalogue order.

        Any that fail to load are skipped rather than breaking the selector: an
        incomplete list beats a window that does not open.
        """
        themes = []

        for name in AVAILABLE_THEMES:
            try:
                themes.append(self._theme_source.load(name))
            except Exception:
                continue

        return themes

    def current(self) -> AppTheme:
        """
        The theme the user saved, or the default on first launch.
        """
        return self._load(self._preferences_repository.load().theme_name)

    def current_name(self) -> str:
        """
        Name of the active theme, to preselect the selector without loading
        the whole palette.
        """
        return self.current().name

    def select(self, theme_name: str) -> AppTheme:
        """
        Sets a theme by name and persists the choice. An unknown name falls
        back to the default instead of failing.
        """
        resolved = theme_name if is_known_theme(theme_name) else DEFAULT_THEME_NAME
        theme = self._load(resolved)

        preferences = self._preferences_repository.load()
        self._preferences_repository.save(preferences.with_theme(theme.name))

        return theme

    def _load(self, theme_name: str) -> AppTheme:
        try:
            return self._theme_source.load(theme_name)
        except Exception:
            if theme_name == DEFAULT_THEME_NAME:
                raise

            return self._theme_source.load(DEFAULT_THEME_NAME)
