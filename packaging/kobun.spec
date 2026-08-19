# -*- mode: python ; coding: utf-8 -*-
"""
Receta de PyInstaller para Kobun, compartida por Linux y Windows.

Se construye con:

    python scripts/build_app.py

PyInstaller **no compila cruzado**: este archivo sirve en los dos sistemas,
pero cada binario hay que generarlo en el sistema al que apunta.
"""
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

RAIZ = Path(SPECPATH).parent  # noqa: F821 — SPECPATH lo inyecta PyInstaller
ES_WINDOWS = sys.platform.startswith("win")

# El flag --onedir de la línea de comandos no llega a un archivo .spec: el modo
# lo decide la receta según tenga o no un paso COLLECT. Se lee del entorno para
# que scripts/build_app.py pueda elegirlo.
UN_SOLO_ARCHIVO = os.environ.get("KOBUN_ONEFILE", "1") != "0"

# Los temas, los iconos y las flechas del selector no son .py, así que sin
# recolectarlos el ejecutable arranca sin colores. Y como ThemeService deja
# pasar la excepción cuando falla el tema por defecto, en realidad no arranca.
DATOS = collect_data_files("kobun.shared")

# Qt trae mucho más de lo que usamos. Cada exclusión se verifica corriendo el
# binario: recortar de más rompe en tiempo de ejecución, no al construir.
QT_SIN_USO = [
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DRender",
    "PySide6.QtBluetooth",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtDesigner",
    "PySide6.QtHelp",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtNfc",
    "PySide6.QtPositioning",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickWidgets",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtSpatialAudio",
    "PySide6.QtSql",
    "PySide6.QtStateMachine",
    "PySide6.QtTest",
    "PySide6.QtTextToSpeech",
    "PySide6.QtWebChannel",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets",
]

EXCLUIDOS = QT_SIN_USO + [
    "tkinter",
    "pytest",
    "setuptools",
    "pip",
]

analysis = Analysis(  # noqa: F821
    [str(RAIZ / "main.py")],
    # Hace falta apuntar al árbol de fuentes: con el proyecto instalado en modo
    # editable, PyInstaller ve el paquete importable pero no encuentra los
    # archivos para empaquetar, y falla con "No module named kobun.…".
    pathex=[str(RAIZ)],
    binaries=[],
    datas=DATOS,
    hiddenimports=[],
    hookspath=[],
    excludes=EXCLUIDOS,
    noarchive=False,
)

pyz = PYZ(analysis.pure)  # noqa: F821

COMUNES = dict(
    name="kobun",
    debug=False,
    strip=False,
    upx=False,
    # Sin consola: es una app de ventana. En Windows evita la terminal negra
    # que aparecería detrás.
    console=False,
    # PyInstaller sólo usa el icono en Windows y macOS; en Linux lo resuelve el
    # escritorio a partir del .desktop.
    icon=str(RAIZ / "kobun" / "shared" / "icons" / "kobun.ico") if ES_WINDOWS else None,
)

if UN_SOLO_ARCHIVO:
    exe = EXE(pyz, analysis.scripts, analysis.binaries, analysis.datas, **COMUNES)  # noqa: F821
else:
    # En modo directorio el ejecutable queda liviano y las dependencias van
    # afuera: arranca más rápido porque no descomprime nada en cada ejecución.
    exe = EXE(pyz, analysis.scripts, exclude_binaries=True, **COMUNES)  # noqa: F821
    coleccion = COLLECT(  # noqa: F821
        exe, analysis.binaries, analysis.datas, strip=False, upx=False, name="kobun",
    )
