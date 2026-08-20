import json
from pathlib import Path
from typing import Optional

from kobun.application.interfaces.theme_source import ThemeSource
from kobun.shared.config.theme_settings import theme_file
from kobun.shared.theme import AppTheme


class ThemeLoader:
    @staticmethod
    def load_from_json(path: Path) -> AppTheme:
        """
        Reads a JSON file and turns it into an AppTheme instance.

        :param path: Path to the theme's .json file.
        :return: An immutable AppTheme instance.
        :raises FileNotFoundError: If the file does not exist.
        :raises ValueError: If the JSON is malformed.
        """
        if not path.exists():
            raise FileNotFoundError(f"No theme file found at: {path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check the minimum structure before instantiating
            if not isinstance(data, dict):
                raise ValueError("A theme file must be a valid JSON object.")

            return AppTheme(
                name=data.get("name", "unknown"),
                colors=data.get("colors", {}),
                label=data.get("label")
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed JSON in the theme file: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error while loading the theme: {str(e)}")

    @staticmethod
    def save_to_json(theme: AppTheme, path: Path) -> None:
        """
        Exports a theme to JSON (useful for the future theme editor).
        """
        data = {
            "name": theme.name,
            "label": theme.label,
            "colors": theme.colors
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)


class JsonThemeSource(ThemeSource):
    """
    Themes read from the JSON files shipped with the application.
    """

    def __init__(self, directory: Optional[Path] = None):
        self._directory = Path(directory) if directory is not None else None

    def load(self, theme_name: str) -> AppTheme:
        path = (
            self._directory / f"{theme_name}.json"
            if self._directory is not None
            else theme_file(theme_name)
        )

        return ThemeLoader.load_from_json(path)