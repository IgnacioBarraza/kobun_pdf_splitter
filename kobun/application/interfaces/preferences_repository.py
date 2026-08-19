from abc import ABC, abstractmethod
from dataclasses import dataclass, replace

from kobun.shared.config.app_settings import DEFAULT_THEME_NAME


@dataclass(frozen=True)
class AppPreferences:
    """
    Preferencias del usuario que sobreviven al cierre de la aplicación.
    """

    theme_name: str = DEFAULT_THEME_NAME

    def with_theme(self, theme_name: str) -> "AppPreferences":
        return replace(self, theme_name=theme_name)


class PreferencesRepository(ABC):
    """
    Persistencia de las preferencias.

    `load` nunca falla: unas preferencias ilegibles se reemplazan por los
    valores por defecto. Que la app no arranque porque el usuario tiene un
    JSON corrupto sería peor que perder su elección de tema.
    """

    @abstractmethod
    def load(self) -> AppPreferences:
        pass

    @abstractmethod
    def save(self, preferences: AppPreferences) -> None:
        pass
