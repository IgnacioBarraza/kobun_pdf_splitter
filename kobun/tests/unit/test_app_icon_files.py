"""
Verifica los archivos del icono sin depender de Qt ni de PyMuPDF: son datos
que viajan con el paquete y deben existir aunque la suite corra pelada.
"""
import struct

import pytest

from kobun.shared.config.app_settings import (
    APP_ICON_SIZES,
    ICONS_DIRECTORY,
    WINDOWS_ICON_FILE,
    app_icon_file,
)

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def read_png_header(path):
    """
    Ancho, alto y tipo de color desde la cabecera IHDR, sin librerías.
    El tipo 6 es RGBA.
    """
    data = path.read_bytes()

    assert data[:8] == PNG_MAGIC, f"{path.name} no es un PNG"
    ancho, alto = struct.unpack(">II", data[16:24])
    tipo_color = data[25]

    return ancho, alto, tipo_color


def test_the_icons_directory_ships_with_the_package():
    assert ICONS_DIRECTORY.is_dir()
    assert ICONS_DIRECTORY.is_absolute(), "debe resolverse relativo al paquete"


@pytest.mark.parametrize("size", APP_ICON_SIZES)
def test_every_declared_size_exists(size):
    assert app_icon_file(size).is_file(), f"falta el icono de {size}px"


@pytest.mark.parametrize("size", APP_ICON_SIZES)
def test_every_icon_is_square_and_matches_its_name(size):
    ancho, alto, _ = read_png_header(app_icon_file(size))

    assert (ancho, alto) == (size, size)


@pytest.mark.parametrize("size", APP_ICON_SIZES)
def test_every_icon_has_transparency(size):
    """
    Regresión: el arte original traía las esquinas en negro sólido, así que el
    icono se veía con un marco negro alrededor del cuadrado redondeado.
    """
    _, _, tipo_color = read_png_header(app_icon_file(size))

    assert tipo_color == 6, f"el icono de {size}px no tiene canal alfa"


def test_the_small_sizes_stay_light():
    """
    Los tamaños chicos se cargan siempre; que uno pese cientos de KB sería
    señal de que se guardó un PNG grande con otro nombre.
    """
    for size in (16, 24, 32, 48):
        peso = app_icon_file(size).stat().st_size
        assert peso < 20_000, f"el icono de {size}px pesa {peso} bytes"


def test_the_windows_icon_bundles_every_size():
    """
    El .ico es un contenedor: cabecera de 6 bytes y una entrada de 16 por
    imagen. Se valida el conteo declarado, no el contenido.
    """
    data = WINDOWS_ICON_FILE.read_bytes()
    reservado, tipo, cantidad = struct.unpack("<HHH", data[:6])

    assert reservado == 0
    assert tipo == 1, "el tipo 1 es icono; 2 sería cursor"
    assert cantidad == len(APP_ICON_SIZES)


def test_the_windows_icon_entries_point_inside_the_file():
    data = WINDOWS_ICON_FILE.read_bytes()
    cantidad = struct.unpack("<H", data[4:6])[0]

    for i in range(cantidad):
        base = 6 + i * 16
        tamano, offset = struct.unpack("<II", data[base + 8:base + 16])

        assert tamano > 0
        assert offset + tamano <= len(data), f"la entrada {i} apunta fuera del archivo"


def test_the_app_id_is_a_valid_desktop_file_name():
    """
    El app_id tiene que servir como nombre de archivo .desktop: en Wayland es
    lo que permite al compositor encontrar el icono de la app.
    """
    from kobun.shared.config.app_settings import APP_ID

    assert APP_ID
    assert APP_ID == APP_ID.lower()
    assert " " not in APP_ID
    assert APP_ID.isascii()
    assert not APP_ID.endswith(".desktop"), "Qt agrega la extensión por su cuenta"


def test_the_windows_installer_version_matches_the_package():
    """
    El instalador declara su versión en su propio archivo. Sin este control,
    publicar un setup etiquetado con una versión vieja no lo nota nadie hasta
    que un usuario lo instala.
    """
    import re
    from pathlib import Path

    import kobun

    iss = Path(__file__).resolve().parents[3] / "packaging" / "kobun.iss"
    if not iss.is_file():
        import pytest as _pytest
        _pytest.skip("no hay receta de instalador")

    declarada = re.search(r'#define MiVersion "([^"]+)"', iss.read_text(encoding="utf-8"))

    assert declarada is not None, "el .iss debe declarar MiVersion"
    assert declarada.group(1) == kobun.__version__


def test_the_windows_installer_points_at_the_bundled_icon():
    """El .ico tiene que existir en el repo: el instalador lo usa como su icono."""
    from pathlib import Path

    import kobun

    raiz = Path(kobun.__file__).resolve().parent.parent
    assert (raiz / "kobun" / "shared" / "icons" / "kobun.ico").is_file()
