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

APP_ID = "kobun"
"""Identificador de aplicación para el escritorio.

En Wayland el compositor no lee el icono de la ventana: identifica la app por
su `app_id` y busca un `<app_id>.desktop` para sacar el icono de ahí. Si no se
declara, Qt usa el nombre del ejecutable —"python3"— y el sistema muestra un
icono genérico.

Tiene que coincidir con el nombre del archivo .desktop instalado."""

HISTORY_FILENAME = "history.json"
PREFERENCES_FILENAME = "preferences.json"

MAX_HISTORY_ENTRIES = 50
"""Tope de exportaciones recordadas. Más allá de esto la lista deja de ser
consultable y el archivo crece sin sentido."""

THEMES_DIRECTORY = Path(__file__).resolve().parent.parent / "themes"
"""Ubicación de los temas incluidos con la app.

Se resuelve relativa al paquete y no al directorio de trabajo: de lo contrario
la app sólo encuentra sus temas si se la lanza desde la raíz del proyecto."""

ICONS_DIRECTORY = Path(__file__).resolve().parent.parent / "icons"
"""Icono de la aplicación, en varios tamaños."""

APP_ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)
"""Tamaños incluidos. Qt elige el más cercano según el contexto —ventana,
barra de tareas, Alt-Tab— y escalar desde uno cercano se ve mejor que
reducir siempre desde el más grande."""


def app_icon_file(size: int) -> Path:
    return ICONS_DIRECTORY / f"kobun_{size}.png"


WINDOWS_ICON_FILE = ICONS_DIRECTORY / "kobun.ico"
"""Icono multi-tamaño para el empaquetado en Windows."""

THEME_ICONS_DIRECTORY = THEMES_DIRECTORY / "icons"
"""Íconos que el QSS necesita como imagen, porque Qt no permite dibujarlos
con estilos: la flecha de los desplegables es el caso típico."""

DEFAULT_THEME_NAME = "light"
