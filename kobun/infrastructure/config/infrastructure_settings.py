import os
import sys
from pathlib import Path
from typing import Mapping, Optional

from kobun.shared.config.app_settings import APP_NAME, APP_SLUG

WINDOWS = "win32"
MACOS = "darwin"


class AppDirectories:
    """
    Resuelve dónde guardar los datos del usuario según el sistema operativo.

    - Windows: %APPDATA%\\Kobun
    - macOS:   ~/Library/Application Support/Kobun
    - Linux y otros: convención XDG, respetando XDG_CONFIG_HOME y XDG_DATA_HOME

    `platform` y `environ` se inyectan para poder verificar las tres
    plataformas desde cualquier máquina: si no, las rutas de Windows y macOS
    quedarían sin tests hasta que alguien las ejecute allí.
    """

    def __init__(
        self,
        app_name: str = APP_NAME,
        app_slug: str = APP_SLUG,
        platform: Optional[str] = None,
        environ: Optional[Mapping[str, str]] = None,
        home: Optional[Path] = None,
    ):
        self._app_name = app_name
        self._app_slug = app_slug
        self._platform = platform if platform is not None else sys.platform
        self._environ = environ if environ is not None else os.environ
        self._home = Path(home) if home is not None else Path.home()

    @property
    def is_windows(self) -> bool:
        return self._platform.startswith(WINDOWS)

    @property
    def is_macos(self) -> bool:
        return self._platform == MACOS

    @property
    def config_dir(self) -> Path:
        """
        Preferencias del usuario: tema elegido, últimas opciones.
        """
        if self.is_windows:
            return self._windows_roaming_dir()

        if self.is_macos:
            return self._macos_support_dir()

        return self._xdg_dir("XDG_CONFIG_HOME", self._home / ".config")

    @property
    def data_dir(self) -> Path:
        """
        Datos generados por la app, como el historial de exportaciones.

        En Windows y macOS coincide con `config_dir`: esas plataformas no
        distinguen configuración de datos como sí hace XDG.
        """
        if self.is_windows:
            return self._windows_roaming_dir()

        if self.is_macos:
            return self._macos_support_dir()

        return self._xdg_dir("XDG_DATA_HOME", self._home / ".local" / "share")

    def config_file(self, filename: str) -> Path:
        return self.config_dir / filename

    def data_file(self, filename: str) -> Path:
        return self.data_dir / filename

    def ensure_config_dir(self) -> Path:
        """
        Crea el directorio de configuración si falta y devuelve su ruta.
        """
        return self._ensure(self.config_dir)

    def ensure_data_dir(self) -> Path:
        """
        Crea el directorio de datos si falta y devuelve su ruta.

        La creación es explícita y no un efecto secundario de leer la
        propiedad: consultar dónde irían los datos no debería tocar el disco.
        """
        return self._ensure(self.data_dir)

    # =========================
    # Internals
    # =========================

    def _windows_roaming_dir(self) -> Path:
        appdata = self._environ.get("APPDATA")
        base = Path(appdata) if appdata else self._home / "AppData" / "Roaming"

        return base / self._app_name

    def _macos_support_dir(self) -> Path:
        return self._home / "Library" / "Application Support" / self._app_name

    def _xdg_dir(self, variable: str, fallback: Path) -> Path:
        """
        La especificación XDG exige ignorar el valor si no es una ruta
        absoluta, cosa que ocurre con variables mal seteadas.
        """
        value = self._environ.get(variable)
        base = Path(value) if value and Path(value).is_absolute() else fallback

        return base / self._app_slug

    @staticmethod
    def _ensure(directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        return directory
