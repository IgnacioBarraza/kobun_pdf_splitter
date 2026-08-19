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
        Lee un archivo JSON y lo convierte en una instancia de AppTheme.

        :param path: Ruta al archivo .json del tema.
        :return: Instancia inmutable de AppTheme.
        :raises FileNotFoundError: Si el archivo no existe.
        :raises ValueError: Si el JSON tiene un formato inválido.
        """
        if not path.exists():
            raise FileNotFoundError(f"No se encontró el archivo de tema en: {path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validamos la estructura mínima antes de instanciar
            if not isinstance(data, dict):
                raise ValueError("El archivo de tema debe ser un objeto JSON válido.")

            return AppTheme(
                name=data.get("name", "unknown"),
                colors=data.get("colors", {}),
                label=data.get("label")
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Error de formato en el JSON del tema: {str(e)}")
        except Exception as e:
            raise Exception(f"Error inesperado al cargar el tema: {str(e)}")

    @staticmethod
    def save_to_json(theme: AppTheme, path: Path) -> None:
        """
        Permite exportar un tema a JSON (útil para el futuro editor de temas).
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
    Temas leídos de los JSON que se distribuyen con la aplicación.
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