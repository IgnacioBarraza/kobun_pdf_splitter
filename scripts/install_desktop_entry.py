#!/usr/bin/env python3
"""
Integra Kobun con el escritorio en Linux.

Hace falta porque en Wayland el compositor no lee el icono de la ventana:
identifica la app por su `app_id` y busca un archivo .desktop con ese nombre
para sacar de ahí el icono y el título. Sin esta instalación, GNOME muestra el
icono genérico de Python por más que la app llame a `setWindowIcon`.

Instala tres cosas en el directorio del usuario, sin permisos de root:

  ~/.local/share/icons/hicolor/<N>x<N>/apps/kobun.png   los iconos
  ~/.local/share/applications/kobun.desktop             la entrada
  y refresca las cachés de GTK

Uso:
    ./.venv/bin/python scripts/install_desktop_entry.py
    ./.venv/bin/python scripts/install_desktop_entry.py --exec dist/kobun
    ./.venv/bin/python scripts/install_desktop_entry.py --uninstall

Sin `--exec` la entrada apunta al intérprete del entorno y a main.py, que es lo
que sirve durante el desarrollo. Con `--exec` apunta a un ejecutable ya
construido, que es lo que corresponde a una app instalada.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from kobun.shared.config.app_settings import (  # noqa: E402
    APP_ICON_SIZES,
    APP_ID,
    APP_NAME,
    app_icon_file,
)

ICONOS = Path.home() / ".local/share/icons/hicolor"
ENTRADAS = Path.home() / ".local/share/applications"
ENTRADA = ENTRADAS / f"{APP_ID}.desktop"

PLANTILLA = """[Desktop Entry]
Type=Application
Version=1.0
Name={nombre}
GenericName=Divisor de PDFs
Comment=Extraer rangos de páginas de un PDF a un archivo nuevo
Exec={comando}
Icon={app_id}
Terminal=false
Categories=Office;
MimeType=application/pdf;
StartupWMClass={app_id}
StartupNotify=true
"""


def linea_exec(ejecutable: Optional[Path]) -> str:
    """
    Comando que el escritorio va a lanzar.

    `%f` es lo que hace que el archivo elegido en "Abrir con" llegue como
    argumento; sin él la app abriría vacía.
    """
    if ejecutable is not None:
        return f"{ejecutable.resolve()} %f"

    # sys.executable es el intérprete que corre este script: si se lo invoca
    # con el del venv, la entrada queda apuntando al correcto.
    return f"{sys.executable} {RAIZ / 'main.py'} %f"


def instalar(ejecutable: Optional[Path] = None) -> None:
    copiados = 0
    for lado in APP_ICON_SIZES:
        origen = app_icon_file(lado)
        if not origen.is_file():
            print(f"  aviso: falta el icono de {lado}px, se omite")
            continue

        destino = ICONOS / f"{lado}x{lado}" / "apps" / f"{APP_ID}.png"
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origen, destino)
        copiados += 1

    print(f"iconos instalados: {copiados} en {ICONOS}")

    ENTRADAS.mkdir(parents=True, exist_ok=True)
    ENTRADA.write_text(
        PLANTILLA.format(nombre=APP_NAME, comando=linea_exec(ejecutable), app_id=APP_ID),
        encoding="utf-8",
    )
    ENTRADA.chmod(0o755)
    print(f"entrada instalada: {ENTRADA}")
    print(f"  Exec={linea_exec(ejecutable)}")

    refrescar()


def desinstalar() -> None:
    quitados = 0
    for lado in APP_ICON_SIZES:
        destino = ICONOS / f"{lado}x{lado}" / "apps" / f"{APP_ID}.png"
        if destino.exists():
            destino.unlink()
            quitados += 1

    if ENTRADA.exists():
        ENTRADA.unlink()
        print(f"entrada eliminada: {ENTRADA}")

    print(f"iconos eliminados: {quitados}")
    refrescar()


def refrescar() -> None:
    """
    Las cachés son opcionales: si faltan las herramientas, el escritorio igual
    encuentra los archivos, sólo puede tardar más en notarlo.
    """
    for comando in (
        ["gtk-update-icon-cache", "-f", "-t", str(ICONOS)],
        ["update-desktop-database", str(ENTRADAS)],
    ):
        if shutil.which(comando[0]) is None:
            continue

        resultado = subprocess.run(comando, capture_output=True, text=True)
        estado = "ok" if resultado.returncode == 0 else "falló (no es crítico)"
        print(f"  {comando[0]}: {estado}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uninstall", action="store_true", help="Quitar la integración")
    parser.add_argument(
        "--exec", dest="ejecutable", type=Path, default=None,
        help="Ruta a un ejecutable construido; por defecto apunta al entorno de desarrollo",
    )
    args = parser.parse_args()

    if args.uninstall:
        desinstalar()
    else:
        if args.ejecutable is not None and not args.ejecutable.is_file():
            raise SystemExit(f"No existe el ejecutable: {args.ejecutable}")

        instalar(args.ejecutable)
        print(f"\nListo. Volvé a lanzar la app; el app_id ahora es '{APP_ID}'.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
