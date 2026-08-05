import json
from pathlib import Path

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
                colors=data.get("colors", {})
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
            "colors": theme.colors
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)