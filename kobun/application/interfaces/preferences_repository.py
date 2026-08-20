from abc import ABC, abstractmethod
from dataclasses import dataclass, replace

from kobun.shared.config.app_settings import DEFAULT_THEME_NAME


@dataclass(frozen=True)
class AppPreferences:
    """
    User preferences that survive closing the application.
    """

    theme_name: str = DEFAULT_THEME_NAME

    def with_theme(self, theme_name: str) -> "AppPreferences":
        return replace(self, theme_name=theme_name)


class PreferencesRepository(ABC):
    """
    Persistence of the preferences.

    `load` never fails: unreadable preferences are replaced by the defaults.
    The app refusing to start because the user has a corrupt JSON would be
    worse than losing their theme choice.
    """

    @abstractmethod
    def load(self) -> AppPreferences:
        pass

    @abstractmethod
    def save(self, preferences: AppPreferences) -> None:
        pass
