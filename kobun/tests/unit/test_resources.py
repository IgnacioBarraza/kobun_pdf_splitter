"""
Every resolution strategy is genuinely exercised, by forcing the previous ones
to fail: otherwise the fallback branches would be code nobody runs until the day
it is packaged and breaks.
"""
from pathlib import Path

import pytest

from kobun.shared import resources as resources
from kobun.shared.config.app_settings import ICONS_DIRECTORY, THEMES_DIRECTORY


@pytest.fixture
def fake_tree(tmp_path):
    """A tree shaped like the package, to simulate a bundle."""
    root = tmp_path / "kobun" / "shared"
    (root / "themes").mkdir(parents=True)
    (root / "themes" / "light.json").write_text("{}", encoding="utf-8")

    return tmp_path


def break_importlib(monkeypatch):
    monkeypatch.setattr(
        resources.resources, "files",
        lambda _package: (_ for _ in ()).throw(ModuleNotFoundError("simulado")),
    )


# =========================
# Camino normal
# =========================

def test_data_root_points_at_the_package_data():
    root = resources.data_root()

    assert root.is_dir()
    assert (root / "themes" / "light.json").is_file()


def test_data_path_joins_parts():
    assert resources.data_path("themes", "light.json").is_file()


def test_app_settings_uses_the_resolved_root():
    assert THEMES_DIRECTORY.is_dir()
    assert ICONS_DIRECTORY.is_dir()


def test_running_from_source_is_not_reported_as_frozen():
    assert resources.is_frozen() is False


# =========================
# Estrategia de ejecutable empaquetado
# =========================

def test_the_frozen_path_is_used_when_importlib_cannot_resolve(monkeypatch, fake_tree):
    break_importlib(monkeypatch)
    monkeypatch.setattr(resources.sys, "frozen", True, raising=False)
    monkeypatch.setattr(resources.sys, "_MEIPASS", str(fake_tree), raising=False)

    assert resources.data_root() == fake_tree / "kobun" / "shared"
    assert resources.is_frozen() is True


def test_meipass_is_ignored_when_the_process_is_not_frozen(monkeypatch, fake_tree):
    """
    A leftover variable without `sys.frozen` must not divert the resolution:
    that happens when something left `_MEIPASS` set in a development
    environment.
    """
    break_importlib(monkeypatch)
    monkeypatch.setattr(resources.sys, "_MEIPASS", str(fake_tree), raising=False)
    monkeypatch.delattr(resources.sys, "frozen", raising=False)

    assert resources.data_root() == Path(resources.__file__).resolve().parent


def test_a_frozen_path_that_does_not_exist_is_skipped(monkeypatch, tmp_path):
    break_importlib(monkeypatch)
    monkeypatch.setattr(resources.sys, "frozen", True, raising=False)
    monkeypatch.setattr(resources.sys, "_MEIPASS", str(tmp_path / "fantasma"), raising=False)

    # It falls back to the module-relative path, which does exist.
    assert resources.data_root() == Path(resources.__file__).resolve().parent


# =========================
# Last resort
# =========================

def test_the_package_relative_path_is_the_last_resort(monkeypatch):
    break_importlib(monkeypatch)
    monkeypatch.delattr(resources.sys, "frozen", raising=False)

    root = resources.data_root()

    assert root == Path(resources.__file__).resolve().parent
    assert (root / "themes" / "light.json").is_file(), "el respaldo debe seguir siendo utilizable"


def test_a_broken_importlib_never_leaks_its_error(monkeypatch):
    """A failure to resolve data must not escape as an import exception."""
    break_importlib(monkeypatch)

    assert resources.data_root().is_dir()
