#!/usr/bin/env python3
"""
Construye el ejecutable de Kobun para el sistema donde se lo ejecuta.

    ./.venv/bin/python scripts/build_app.py
    ./.venv/bin/python scripts/build_app.py --onedir

PyInstaller **no compila cruzado**: el .exe de Windows hay que generarlo en
Windows y el binario de Linux en Linux. Este script es el mismo en los dos; lo
que cambia es dónde se corre.

Requiere el extra de construcción:

    pip install -e .[build]
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SPEC = RAIZ / "packaging" / "kobun.spec"
SALIDA = RAIZ / "dist"
TRABAJO = RAIZ / "build"

NOMBRE_BINARIO = "kobun.exe" if sys.platform.startswith("win") else "kobun"


def verificar_entorno() -> None:
    if not SPEC.is_file():
        raise SystemExit(f"No se encuentra la receta: {SPEC}")

    if shutil.which("pyinstaller") is None and not _pyinstaller_importable():
        raise SystemExit(
            "PyInstaller no está instalado.\n"
            "Instalalo con:  pip install -e .[build]"
        )


def _pyinstaller_importable() -> bool:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        return False

    return True


def construir(onedir: bool, limpiar: bool) -> Path:
    if limpiar:
        for directorio in (SALIDA, TRABAJO):
            if directorio.exists():
                shutil.rmtree(directorio)
                print(f"  limpiado {directorio.relative_to(RAIZ)}/")

    comando = [
        sys.executable, "-m", "PyInstaller",
        str(SPEC),
        "--distpath", str(SALIDA),
        "--workpath", str(TRABAJO),
        "--noconfirm",
        "--log-level", "WARN",
    ]

    # El flag --onedir no llega a un archivo .spec: la receta lee el modo del
    # entorno. Pasarlo como flag no hacía nada.
    entorno = dict(os.environ, KOBUN_ONEFILE="0" if onedir else "1")

    print(f"\nConstruyendo para {sys.platform} ({'directorio' if onedir else 'un solo archivo'})...")
    inicio = time.monotonic()
    resultado = subprocess.run(comando, cwd=RAIZ, env=entorno)
    duracion = time.monotonic() - inicio

    if resultado.returncode != 0:
        raise SystemExit(f"\nLa construcción falló (código {resultado.returncode}).")

    print(f"Terminado en {duracion:.0f}s")

    return SALIDA / NOMBRE_BINARIO


def informar(binario: Path) -> None:
    if binario.is_file():
        mb = binario.stat().st_size / 1024 / 1024
        print(f"\nEjecutable: {binario}  ({mb:.0f} MB)")
    elif binario.parent.is_dir():
        total = sum(f.stat().st_size for f in binario.parent.rglob("*") if f.is_file())
        print(f"\nDirectorio: {binario.parent}  ({total / 1024 / 1024:.0f} MB)")
    else:
        raise SystemExit(f"\nNo se encontró la salida esperada en {binario}")

    print(
        "\nProbalo antes de distribuirlo: un ejecutable puede construirse sin "
        "errores y fallar al arrancar por un módulo de Qt excluido de más."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--onedir", action="store_true",
        help="Genera un directorio en vez de un único archivo (arranca más rápido)",
    )
    parser.add_argument(
        "--keep", action="store_true",
        help="No borrar dist/ y build/ antes de construir",
    )
    args = parser.parse_args()

    verificar_entorno()
    informar(construir(onedir=args.onedir, limpiar=not args.keep))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
