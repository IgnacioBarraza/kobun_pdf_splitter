"""
Application constants: identity, filenames and limits.

These are values several layers need to know and that depend on neither the
operating system nor the environment. Resolving concrete paths lives in
`infrastructure.config.infrastructure_settings`.
"""
from pathlib import Path

from kobun.shared.resources import data_path

APP_NAME = "Kobun"
"""Display name. Used as the folder name on Windows and macOS, where the
convention is capitalised."""

APP_SLUG = "kobun"
"""Lowercase identifier, for XDG-style paths on Linux."""

APP_ID = "kobun"
"""Application identifier for the desktop.

On Wayland the compositor does not read the icon from the window: it identifies
the app by its `app_id` and looks for an `<app_id>.desktop` to take the icon
from. Without declaring it, Qt uses the executable's name —"python3"— and the
system shows a generic icon.

It has to match the name of the installed .desktop file."""

HISTORY_FILENAME = "history.json"
PREFERENCES_FILENAME = "preferences.json"

MAX_HISTORY_ENTRIES = 50
"""Cap on remembered exports. Past this the list stops being browsable and
the file grows for nothing."""

THEMES_DIRECTORY = data_path("themes")
"""Where the themes shipped with the app live.

Resolved against the package and not against the working directory or this
file's path: that way it still holds inside a frozen executable, where code and
data do not sit next to each other."""

ICONS_DIRECTORY = data_path("icons")
"""The application icon, in several sizes."""

APP_ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)
"""Sizes shipped. Qt picks the closest one for the context —window, taskbar,
Alt-Tab— and scaling from a nearby size looks better than always shrinking the
largest one."""


def app_icon_file(size: int) -> Path:
    return ICONS_DIRECTORY / f"kobun_{size}.png"


WINDOWS_ICON_FILE = ICONS_DIRECTORY / "kobun.ico"
"""Multi-size icon for the Windows packaging."""

THEME_ICONS_DIRECTORY = THEMES_DIRECTORY / "icons"
"""Icons the QSS needs as images, because Qt does not allow drawing them with
styles: the combo box arrow is the typical case."""

DEFAULT_THEME_NAME = "light"
