"""
Cada estrategia de resolución se ejercita de verdad, forzando el fallo de las
anteriores: si no, las ramas de contención serían código que nadie corre hasta
el día que se empaqueta y falla.
"""
from pathlib import Path

import pytest

from kobun.shared import resources as recursos
from kobun.shared.config.app_settings import ICONS_DIRECTORY, THEMES_DIRECTORY


@pytest.fixture
def arbol_falso(tmp_path):
    """Un árbol con la misma forma que el paquete, para simular un bundle."""
    raiz = tmp_path / "kobun" / "shared"
    (raiz / "themes").mkdir(parents=True)
    (raiz / "themes" / "light.json").write_text("{}", encoding="utf-8")

    return tmp_path


def romper_importlib(monkeypatch):
    monkeypatch.setattr(
        recursos.resources, "files",
        lambda _paquete: (_ for _ in ()).throw(ModuleNotFoundError("simulado")),
    )


# =========================
# Camino normal
# =========================

def test_data_root_points_at_the_package_data():
    raiz = recursos.data_root()

    assert raiz.is_dir()
    assert (raiz / "themes" / "light.json").is_file()


def test_data_path_joins_parts():
    assert recursos.data_path("themes", "light.json").is_file()


def test_app_settings_uses_the_resolved_root():
    assert THEMES_DIRECTORY.is_dir()
    assert ICONS_DIRECTORY.is_dir()


def test_running_from_source_is_not_reported_as_frozen():
    assert recursos.is_frozen() is False


# =========================
# Estrategia de ejecutable empaquetado
# =========================

def test_the_frozen_path_is_used_when_importlib_cannot_resolve(monkeypatch, arbol_falso):
    romper_importlib(monkeypatch)
    monkeypatch.setattr(recursos.sys, "frozen", True, raising=False)
    monkeypatch.setattr(recursos.sys, "_MEIPASS", str(arbol_falso), raising=False)

    assert recursos.data_root() == arbol_falso / "kobun" / "shared"
    assert recursos.is_frozen() is True


def test_meipass_is_ignored_when_the_process_is_not_frozen(monkeypatch, arbol_falso):
    """
    Una variable colgada sin `sys.frozen` no debe desviar la resolución: pasa
    si algo dejó `_MEIPASS` puesto en el entorno de desarrollo.
    """
    romper_importlib(monkeypatch)
    monkeypatch.setattr(recursos.sys, "_MEIPASS", str(arbol_falso), raising=False)
    monkeypatch.delattr(recursos.sys, "frozen", raising=False)

    assert recursos.data_root() == Path(recursos.__file__).resolve().parent


def test_a_frozen_path_that_does_not_exist_is_skipped(monkeypatch, tmp_path):
    romper_importlib(monkeypatch)
    monkeypatch.setattr(recursos.sys, "frozen", True, raising=False)
    monkeypatch.setattr(recursos.sys, "_MEIPASS", str(tmp_path / "fantasma"), raising=False)

    # Cae en la ruta relativa al módulo, que sí existe.
    assert recursos.data_root() == Path(recursos.__file__).resolve().parent


# =========================
# Último recurso
# =========================

def test_the_package_relative_path_is_the_last_resort(monkeypatch):
    romper_importlib(monkeypatch)
    monkeypatch.delattr(recursos.sys, "frozen", raising=False)

    raiz = recursos.data_root()

    assert raiz == Path(recursos.__file__).resolve().parent
    assert (raiz / "themes" / "light.json").is_file(), "el respaldo debe seguir siendo utilizable"


def test_a_broken_importlib_never_leaks_its_error(monkeypatch):
    """Un fallo al resolver datos no puede escapar como excepción de import."""
    romper_importlib(monkeypatch)

    assert recursos.data_root().is_dir()
