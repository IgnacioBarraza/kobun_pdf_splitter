from abc import ABC, abstractmethod

from kobun.shared.theme import AppTheme


class ThemeSource(ABC):
    """
    De dónde salen los temas.

    Existe para que ThemeService no dependa de que los temas vivan en archivos
    JSON: mañana podrían venir de un editor de temas del usuario o de recursos
    embebidos en el ejecutable empaquetado.
    """

    @abstractmethod
    def load(self, theme_name: str) -> AppTheme:
        """
        :raises Exception: Si el tema no existe o no se puede interpretar.
        """
        pass
