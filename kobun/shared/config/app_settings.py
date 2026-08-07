"""
Constantes de la aplicación: identidad, nombres de archivo y límites.

Son valores que varias capas necesitan conocer y que no dependen del sistema
operativo ni del entorno. La resolución de rutas concretas vive en
`infrastructure.config.infrastructure_settings`.
"""
from pathlib import Path

APP_NAME = "Kobun"
"""Nombre visible. Se usa como nombre de carpeta en Windows y macOS, donde la
convención es capitalizada."""

APP_SLUG = "kobun"
"""Identificador en minúsculas, para rutas estilo XDG en Linux."""

HISTORY_FILENAME = "history.json"
PREFERENCES_FILENAME = "preferences.json"

MAX_HISTORY_ENTRIES = 50
"""Tope de exportaciones recordadas. Más allá de esto la lista deja de ser
consultable y el archivo crece sin sentido."""

THEMES_DIRECTORY = Path(__file__).resolve().parent.parent / "themes"
"""Ubicación de los temas incluidos con la app.

Se resuelve relativa al paquete y no al directorio de trabajo: de lo contrario
la app sólo encuentra sus temas si se la lanza desde la raíz del proyecto."""

THEME_ICONS_DIRECTORY = THEMES_DIRECTORY / "icons"
"""Íconos que el QSS necesita como imagen, porque Qt no permite dibujarlos
con estilos: la flecha de los desplegables es el caso típico."""

DEFAULT_THEME_NAME = "light"
