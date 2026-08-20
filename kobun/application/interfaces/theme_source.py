from abc import ABC, abstractmethod

from kobun.shared.theme import AppTheme


class ThemeSource(ABC):
    """
    Where themes come from.

    It exists so ThemeService does not depend on themes living in JSON files:
    tomorrow they could come from a user theme editor or from resources
    embedded in the frozen executable.
    """

    @abstractmethod
    def load(self, theme_name: str) -> AppTheme:
        """
        :raises Exception: If the theme does not exist or cannot be parsed.
        """
        pass
