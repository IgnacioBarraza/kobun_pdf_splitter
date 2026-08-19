#!/usr/bin/env python3
"""
Empaqueta el ejecutable de Linux en un .deb instalable.

    ./.venv/bin/python scripts/build_app.py
    ./.venv/bin/python scripts/build_deb.py

Es el equivalente del instalador de Windows: un ejecutable suelto no alcanza en
Linux moderno porque los exploradores de archivos ya no lanzan binarios con
doble clic —GNOME lo desactivó por seguridad— así que hace falta instalarlo con
su entrada .desktop para que aparezca en el menú de aplicaciones.

El resultado queda en dist/kobun_<version>_amd64.deb y se instala con:

    sudo apt install ./dist/kobun_<version>_amd64.deb
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import kobun  # noqa: E402
from kobun.shared.config.app_settings import APP_ICON_SIZES, APP_ID, APP_NAME, app_icon_file  # noqa: E402

ARQUITECTURA = "amd64"
MANTENEDOR = "Ignacio Barraza <ignacio@mapvx.com>"

# Medidas, no adivinadas: son las librerías que las .so del bundle de Qt
# necesitan y que el propio bundle no trae. Se obtienen recorriendo los NEEDED
# de cada biblioteca empaquetada y mapeándolos a paquetes con dpkg -S.
DEPENDENCIAS = [
    "libc6",
    "libdrm2",
    "libegl1",
    "libgl1",
    "libwayland-client0",
    "libwayland-cursor0",
    "libwayland-egl1",
    "libxcb1",
]

DESCRIPCION = """Utilidad de escritorio para dividir PDFs por rangos de páginas
 Kobun extrae rangos de páginas de un PDF —incluso discontinuos, como
 1-5,10-15,20— a un archivo nuevo, sin tocar el original.
 .
 Incluye historial de exportaciones y diez temas visuales."""

CONTROL = """Package: {paquete}
Version: {version}
Section: utils
Priority: optional
Architecture: {arquitectura}
Depends: {dependencias}
Installed-Size: {tamano}
Maintainer: {mantenedor}
Homepage: https://github.com/IgnacioBarraza/kobun_pdf_splitter
Description: {descripcion}
"""

DESKTOP = """[Desktop Entry]
Type=Application
Version=1.0
Name={nombre}
GenericName=Divisor de PDFs
Comment=Extraer rangos de páginas de un PDF a un archivo nuevo
Exec=/usr/bin/{app_id} %f
Icon={app_id}
Terminal=false
Categories=Office;
MimeType=application/pdf;
StartupWMClass={app_id}
StartupNotify=true
"""

# Las cachés del escritorio no se actualizan solas: sin esto el icono puede no
# aparecer hasta el siguiente inicio de sesión.
POSTINST = """#!/bin/sh
set -e
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
"""

POSTRM = POSTINST


def preparar_arbol(destino: Path, binario: Path) -> None:
    (destino / "DEBIAN").mkdir(parents=True)
    bin_dir = destino / "usr" / "bin"
    bin_dir.mkdir(parents=True)

    ejecutable = bin_dir / APP_ID
    shutil.copy2(binario, ejecutable)
    ejecutable.chmod(0o755)

    apps = destino / "usr" / "share" / "applications"
    apps.mkdir(parents=True)
    entrada = apps / f"{APP_ID}.desktop"
    entrada.write_text(DESKTOP.format(nombre=APP_NAME, app_id=APP_ID), encoding="utf-8")
    # La política de Debian pide 644 en los archivos de datos; el umask del
    # entorno de construcción puede dejarlos con permiso de grupo.
    entrada.chmod(0o644)

    for lado in APP_ICON_SIZES:
        origen = app_icon_file(lado)
        if not origen.is_file():
            continue
        carpeta = destino / "usr" / "share" / "icons" / "hicolor" / f"{lado}x{lado}" / "apps"
        carpeta.mkdir(parents=True, exist_ok=True)
        icono = carpeta / f"{APP_ID}.png"
        shutil.copy2(origen, icono)
        icono.chmod(0o644)

    # La licencia es obligatoria según la política de Debian.
    doc = destino / "usr" / "share" / "doc" / APP_ID
    doc.mkdir(parents=True)
    licencia = doc / "copyright"
    shutil.copy2(RAIZ / "LICENSE", licencia)
    licencia.chmod(0o644)


def escribir_control(destino: Path) -> None:
    kb = sum(f.stat().st_size for f in destino.rglob("*") if f.is_file()) // 1024

    (destino / "DEBIAN" / "control").write_text(
        CONTROL.format(
            paquete=APP_ID,
            version=kobun.__version__,
            arquitectura=ARQUITECTURA,
            dependencias=", ".join(DEPENDENCIAS),
            tamano=kb,
            mantenedor=MANTENEDOR,
            descripcion=DESCRIPCION,
        ),
        encoding="utf-8",
    )

    for nombre, contenido in (("postinst", POSTINST), ("postrm", POSTRM)):
        script = destino / "DEBIAN" / nombre
        script.write_text(contenido, encoding="utf-8")
        script.chmod(0o755)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--binary", type=Path, default=RAIZ / "dist" / "kobun",
        help="Ejecutable a empaquetar (por defecto dist/kobun)",
    )
    args = parser.parse_args()

    if sys.platform.startswith("win"):
        raise SystemExit("Un .deb sólo tiene sentido en Linux.")

    if shutil.which("dpkg-deb") is None:
        raise SystemExit("Falta dpkg-deb. Instalalo con: sudo apt install dpkg-dev")

    binario = args.binary
    if binario.is_dir():
        binario = binario / "kobun"

    if not binario.is_file():
        raise SystemExit(
            f"No se encuentra el ejecutable en {binario}.\n"
            "Construilo primero con: python scripts/build_app.py"
        )

    trabajo = RAIZ / "build" / "deb"
    if trabajo.exists():
        shutil.rmtree(trabajo)

    preparar_arbol(trabajo, binario)
    escribir_control(trabajo)

    salida = RAIZ / "dist" / f"{APP_ID}_{kobun.__version__}_{ARQUITECTURA}.deb"
    subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(trabajo), str(salida)],
                   check=True)

    print(f"\nPaquete: {salida}  ({salida.stat().st_size / 1024 / 1024:.0f} MB)")
    print(f"Instalar:    sudo apt install {salida}")
    print(f"Desinstalar: sudo apt remove {APP_ID}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
