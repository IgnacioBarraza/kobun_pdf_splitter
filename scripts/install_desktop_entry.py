#!/usr/bin/env python3
"""
Integrates Kobun with the desktop on Linux.

It is needed because on Wayland the compositor does not read the icon from the
window: it identifies the app by its `app_id` and looks for a .desktop file
with that name to take the icon and the title from. Without this installation,
GNOME shows Python's generic icon no matter how often the app calls
`setWindowIcon`.

It installs three things into the user's directory, with no root permissions:

  ~/.local/share/icons/hicolor/<N>x<N>/apps/kobun.png   the icons
  ~/.local/share/applications/kobun.desktop             the entry
  and it refreshes the GTK caches

Usage:
    ./.venv/bin/python scripts/install_desktop_entry.py
    ./.venv/bin/python scripts/install_desktop_entry.py --exec dist/kobun
    ./.venv/bin/python scripts/install_desktop_entry.py --uninstall

Without `--exec` the entry points at the environment's interpreter and main.py,
which is what serves during development. With `--exec` it points at an already
built executable, which is what an installed app should look like.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kobun.shared.config.app_settings import (  # noqa: E402
    APP_ICON_SIZES,
    APP_ID,
    APP_NAME,
    app_icon_file,
)

ICONS_DIR = Path.home() / ".local/share/icons/hicolor"
ENTRIES_DIR = Path.home() / ".local/share/applications"
ENTRY = ENTRIES_DIR / f"{APP_ID}.desktop"

# The Name, GenericName and Comment are what the user reads in their
# application menu, so they stay in the language of the interface.
TEMPLATE = """[Desktop Entry]
Type=Application
Version=1.0
Name={name}
GenericName=Divisor de PDFs
Comment=Extraer rangos de páginas de un PDF a un archivo nuevo
Exec={command}
Icon={app_id}
Terminal=false
Categories=Office;
MimeType=application/pdf;
StartupWMClass={app_id}
StartupNotify=true
"""


def exec_line(executable: Optional[Path]) -> str:
    """
    The command the desktop will launch.

    `%f` is what makes the file chosen through "Open with" arrive as an
    argument; without it the app would open empty.
    """
    if executable is not None:
        return f"{executable.resolve()} %f"

    # sys.executable is the interpreter running this script: invoked with the
    # venv's one, the entry ends up pointing at the right interpreter.
    return f"{sys.executable} {ROOT / 'main.py'} %f"


def install(executable: Optional[Path] = None) -> None:
    copied = 0
    for side in APP_ICON_SIZES:
        source = app_icon_file(side)
        if not source.is_file():
            print(f"  warning: the {side}px icon is missing, skipping it")
            continue

        destination = ICONS_DIR / f"{side}x{side}" / "apps" / f"{APP_ID}.png"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied += 1

    print(f"icons installed: {copied} in {ICONS_DIR}")

    ENTRIES_DIR.mkdir(parents=True, exist_ok=True)
    ENTRY.write_text(
        TEMPLATE.format(name=APP_NAME, command=exec_line(executable), app_id=APP_ID),
        encoding="utf-8",
    )
    ENTRY.chmod(0o755)
    print(f"entry installed: {ENTRY}")
    print(f"  Exec={exec_line(executable)}")

    refresh()


def uninstall() -> None:
    removed = 0
    for side in APP_ICON_SIZES:
        destination = ICONS_DIR / f"{side}x{side}" / "apps" / f"{APP_ID}.png"
        if destination.exists():
            destination.unlink()
            removed += 1

    if ENTRY.exists():
        ENTRY.unlink()
        print(f"entry removed: {ENTRY}")

    print(f"icons removed: {removed}")
    refresh()


def refresh() -> None:
    """
    The caches are optional: with the tools missing the desktop still finds the
    files, it may just take longer to notice them.
    """
    for command in (
        ["gtk-update-icon-cache", "-f", "-t", str(ICONS_DIR)],
        ["update-desktop-database", str(ENTRIES_DIR)],
    ):
        if shutil.which(command[0]) is None:
            continue

        result = subprocess.run(command, capture_output=True, text=True)
        status = "ok" if result.returncode == 0 else "failed (not critical)"
        print(f"  {command[0]}: {status}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uninstall", action="store_true", help="Remove the integration")
    parser.add_argument(
        "--exec", dest="executable", type=Path, default=None,
        help="Path to a built executable; defaults to pointing at the development environment",
    )
    args = parser.parse_args()

    if args.uninstall:
        uninstall()
    else:
        if args.executable is not None and not args.executable.is_file():
            raise SystemExit(f"No such executable: {args.executable}")

        install(args.executable)
        print(f"\nDone. Relaunch the app; the app_id is now '{APP_ID}'.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
