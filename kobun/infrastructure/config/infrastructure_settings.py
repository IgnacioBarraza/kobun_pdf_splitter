import os
import sys
from pathlib import Path
from typing import Mapping, Optional

from kobun.shared.config.app_settings import APP_NAME, APP_SLUG

WINDOWS = "win32"
MACOS = "darwin"


class AppDirectories:
    """
    Resolves where to keep the user's data, per operating system.

    - Windows: %APPDATA%\\Kobun
    - macOS:   ~/Library/Application Support/Kobun
    - Linux and others: the XDG convention, honouring XDG_CONFIG_HOME and
      XDG_DATA_HOME

    `platform` and `environ` are injected so all three platforms can be
    verified from any machine: otherwise the Windows and macOS paths would go
    untested until someone runs them there.
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
        User preferences: chosen theme, last options used.
        """
        if self.is_windows:
            return self._windows_roaming_dir()

        if self.is_macos:
            return self._macos_support_dir()

        return self._xdg_dir("XDG_CONFIG_HOME", self._home / ".config")

    @property
    def data_dir(self) -> Path:
        """
        Data the app generates, such as the export history.

        On Windows and macOS this matches `config_dir`: those platforms do not
        separate configuration from data the way XDG does.
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
        Creates the configuration directory if missing and returns its path.
        """
        return self._ensure(self.config_dir)

    def ensure_data_dir(self) -> Path:
        """
        Creates the data directory if missing and returns its path.

        Creating it is explicit and not a side effect of reading the property:
        asking where data would go should not touch the disk.
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
        The XDG specification requires ignoring the value when it is not an
        absolute path, which happens with badly set variables.
        """
        value = self._environ.get(variable)
        base = Path(value) if value and Path(value).is_absolute() else fallback

        return base / self._app_slug

    @staticmethod
    def _ensure(directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        return directory
