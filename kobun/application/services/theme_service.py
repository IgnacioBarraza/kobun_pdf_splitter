from typing import List

from kobun.application.interfaces.preferences_repository import PreferencesRepository
from kobun.application.interfaces.theme_source import ThemeSource
from kobun.shared.config.app_settings import DEFAULT_THEME_NAME
from kobun.shared.config.theme_settings import AVAILABLE_THEMES, is_known_theme
from kobun.shared.theme import AppTheme


class ThemeService:
    """
    Resuelve qué tema mostrar, ofrece el catálogo y recuerda la elección.

    Cargar un tema no falla hacia afuera mientras el tema por defecto siga
    siendo legible: un JSON roto o un nombre desconocido caen al default. Un
    color mal puesto no puede dejar la ventana sin dibujar.
    """

    def __init__(self, preferences_repository: PreferencesRepository, theme_source: ThemeSource):
        self._preferences_repository = preferences_repository
        self._theme_source = theme_source

    def available(self) -> List[AppTheme]:
        """
        Temas ofrecidos al usuario, en el orden del catálogo.

        Los que no se puedan cargar se omiten en vez de romper el selector:
        vale más una lista incompleta que una ventana que no abre.
        """
        temas = []

        for name in AVAILABLE_THEMES:
            try:
                temas.append(self._theme_source.load(name))
            except Exception:
                continue

        return temas

    def current(self) -> AppTheme:
        """
        Tema guardado por el usuario, o el por defecto en el primer arranque.
        """
        return self._load(self._preferences_repository.load().theme_name)

    def current_name(self) -> str:
        """
        Nombre del tema activo, para preseleccionar el selector sin tener que
        cargar la paleta entera.
        """
        return self.current().name

    def select(self, theme_name: str) -> AppTheme:
        """
        Fija un tema por nombre y persiste la elección. Un nombre desconocido
        cae al por defecto en vez de fallar.
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
