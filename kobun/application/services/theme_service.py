from kobun.application.interfaces.preferences_repository import PreferencesRepository
from kobun.application.interfaces.theme_source import ThemeSource
from kobun.shared.config.app_settings import DEFAULT_THEME_NAME
from kobun.shared.config.theme_settings import is_known_theme, opposite_theme
from kobun.shared.theme import AppTheme


class ThemeService:
    """
    Resuelve qué tema mostrar y recuerda la elección del usuario.

    Cargar un tema no falla hacia afuera mientras el tema por defecto siga
    siendo legible: un JSON roto o un nombre desconocido caen al default. Un
    color mal puesto no puede dejar la ventana sin dibujar.
    """

    def __init__(self, preferences_repository: PreferencesRepository, theme_source: ThemeSource):
        self._preferences_repository = preferences_repository
        self._theme_source = theme_source

    def current(self) -> AppTheme:
        """
        Tema guardado por el usuario, o el por defecto en el primer arranque.
        """
        return self._load(self._preferences_repository.load().theme_name)

    def toggle(self) -> AppTheme:
        """
        Alterna entre claro y oscuro, persiste la elección y devuelve el tema
        ya cargado.
        """
        preferences = self._preferences_repository.load()

        return self.select(opposite_theme(preferences.theme_name))

    def select(self, theme_name: str) -> AppTheme:
        """
        Fija un tema por nombre. Un nombre desconocido cae al por defecto en
        vez de fallar.
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
