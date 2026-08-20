import os

import pytest

from kobun.domain.pdf.exceptions.file_open_exception import FileOpenException
from kobun.domain.pdf.exceptions.invalid_output_path_exception import InvalidOutputPathException
from kobun.infrastructure.filesystem.local_file_storage import LocalFileStorage


@pytest.fixture
def storage():
    return LocalFileStorage()


def test_exists_and_type_predicates(storage, tmp_path):
    file = tmp_path / "a.pdf"
    file.write_bytes(b"x")

    assert storage.exists(file)
    assert storage.is_file(file)
    assert not storage.is_directory(file)

    assert storage.is_directory(tmp_path)
    assert not storage.is_file(tmp_path)
    assert not storage.exists(tmp_path / "fantasma.pdf")


def test_is_same_file_for_existing_paths(storage, tmp_path):
    file = tmp_path / "a.pdf"
    file.write_bytes(b"x")

    assert storage.is_same_file(file, tmp_path / "sub" / ".." / "a.pdf")
    assert not storage.is_same_file(file, tmp_path / "b.pdf")


def test_is_same_file_for_paths_that_do_not_exist(storage, tmp_path):
    assert storage.is_same_file(tmp_path / "x.pdf", tmp_path / "./x.pdf")
    assert not storage.is_same_file(tmp_path / "x.pdf", tmp_path / "y.pdf")


def test_is_same_file_follows_symlinks(storage, tmp_path):
    original = tmp_path / "real.pdf"
    original.write_bytes(b"x")
    link = tmp_path / "link.pdf"
    link.symlink_to(original)

    assert storage.is_same_file(original, link)


def test_ensure_writable_directory_accepts_a_normal_directory(storage, tmp_path):
    storage.ensure_writable_directory(tmp_path)


def test_ensure_writable_directory_rejects_missing_and_non_directory(storage, tmp_path):
    file = tmp_path / "a.pdf"
    file.write_bytes(b"x")

    with pytest.raises(InvalidOutputPathException, match="no existe"):
        storage.ensure_writable_directory(tmp_path / "fantasma")

    with pytest.raises(InvalidOutputPathException, match="no es un directorio"):
        storage.ensure_writable_directory(file)


def test_unique_path_returns_the_same_path_when_free(storage, tmp_path):
    libre = tmp_path / "out.pdf"

    assert storage.unique_path(libre) == libre


def test_unique_path_skips_taken_names(storage, tmp_path):
    (tmp_path / "out.pdf").write_bytes(b"x")
    assert storage.unique_path(tmp_path / "out.pdf") == tmp_path / "out_1.pdf"

    (tmp_path / "out_1.pdf").write_bytes(b"x")
    assert storage.unique_path(tmp_path / "out.pdf") == tmp_path / "out_2.pdf"


def test_unique_path_preserves_suffix_and_parent(storage, tmp_path):
    sub = tmp_path / "exports"
    sub.mkdir()
    (sub / "book_1-5.pdf").write_bytes(b"x")

    result = storage.unique_path(sub / "book_1-5.pdf")

    assert result.parent == sub
    assert result.name == "book_1-5_1.pdf"


# =========================
# Apertura con la app del sistema
# =========================

class SpawnRecorder:
    """Reemplaza el lanzamiento real de procesos y registra el comando."""

    def __init__(self, error: Exception = None):
        self.commands = []
        self._error = error

    def __call__(self, command):
        self.commands.append(list(command))
        if self._error is not None:
            raise self._error


@pytest.fixture
def file(tmp_path):
    path = tmp_path / "export.pdf"
    path.write_bytes(b"%PDF")
    return path


def test_linux_uses_xdg_open(file):
    recorder = SpawnRecorder()

    LocalFileStorage(platform="linux", spawn=recorder).open_in_default_app(file)

    assert recorder.commands == [["xdg-open", str(file)]]


def test_macos_uses_open(file):
    recorder = SpawnRecorder()

    LocalFileStorage(platform="darwin", spawn=recorder).open_in_default_app(file)

    assert recorder.commands == [["open", str(file)]]


def test_windows_uses_the_system_api_not_a_command(file, monkeypatch):
    llamadas = []
    monkeypatch.setattr(os, "startfile", llamadas.append, raising=False)
    recorder = SpawnRecorder()

    LocalFileStorage(platform="win32", spawn=recorder).open_in_default_app(file)

    assert llamadas == [str(file)]
    assert recorder.commands == [], "Windows no debe pasar por subprocess"


def test_missing_file_is_reported_before_launching_anything(tmp_path):
    recorder = SpawnRecorder()
    storage = LocalFileStorage(platform="linux", spawn=recorder)

    with pytest.raises(FileOpenException, match="ya no está disponible"):
        storage.open_in_default_app(tmp_path / "borrado.pdf")

    assert recorder.commands == []


def test_a_directory_cannot_be_opened_as_a_file(tmp_path):
    folder = tmp_path / "carpeta.pdf"
    folder.mkdir()

    with pytest.raises(FileOpenException, match="ya no está disponible"):
        LocalFileStorage(platform="linux", spawn=SpawnRecorder()).open_in_default_app(folder)


def test_a_missing_opener_becomes_a_domain_exception(file):
    """A system without xdg-open installed must not blow up with FileNotFoundError."""
    recorder = SpawnRecorder(error=FileNotFoundError("xdg-open"))
    storage = LocalFileStorage(platform="linux", spawn=recorder)

    with pytest.raises(FileOpenException, match="No se pudo abrir 'export.pdf'"):
        storage.open_in_default_app(file)


def test_the_original_error_is_preserved_as_cause(file):
    original = OSError("permiso denegado")
    storage = LocalFileStorage(platform="linux", spawn=SpawnRecorder(error=original))

    with pytest.raises(FileOpenException) as error:
        storage.open_in_default_app(file)

    assert error.value.__cause__ is original


def test_open_command_is_inspectable_without_launching(file):
    assert LocalFileStorage(platform="linux").open_command(file) == ["xdg-open", str(file)]
    assert LocalFileStorage(platform="darwin").open_command(file) == ["open", str(file)]


def test_default_construction_still_works():
    """The rest of the code builds LocalFileStorage() with no arguments."""
    storage = LocalFileStorage()

    assert isinstance(storage.is_windows, bool)
