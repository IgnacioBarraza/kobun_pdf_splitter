import json
import os
from pathlib import Path

from kobun.application.interfaces.preferences_repository import (
    AppPreferences,
    PreferencesRepository,
)
from kobun.shared.config.app_settings import DEFAULT_THEME_NAME
from kobun.shared.config.theme_settings import is_known_theme

SCHEMA_VERSION = 1


class JsonPreferencesRepository(PreferencesRepository):
    """
    Preferences in a JSON file inside the user's configuration directory.

    It writes atomically, like the history: a lost preference is trivial, but a
    truncated file would break the next launch.
    """

    def __init__(self, file_path: Path):
        self._file_path = Path(file_path)

    @property
    def file_path(self) -> Path:
        return self._file_path

    def load(self) -> AppPreferences:
        if not self._file_path.exists():
            return AppPreferences()

        try:
            with open(self._file_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            return AppPreferences()

        if not isinstance(payload, dict):
            return AppPreferences()

        theme_name = payload.get("theme_name")
        if not isinstance(theme_name, str) or not is_known_theme(theme_name):
            theme_name = DEFAULT_THEME_NAME

        return AppPreferences(theme_name=theme_name)

    def save(self, preferences: AppPreferences) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "version": SCHEMA_VERSION,
            "theme_name": preferences.theme_name,
        }

        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")

        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

        os.replace(temporary, self._file_path)
