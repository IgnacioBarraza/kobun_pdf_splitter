import pytest

from kobun.domain.pdf.exceptions.invalid_output_path_exception import InvalidOutputPathException
from kobun.infrastructure.filesystem.local_file_storage import LocalFileStorage


@pytest.fixture
def storage():
    return LocalFileStorage()


def test_exists_and_type_predicates(storage, tmp_path):
    archivo = tmp_path / "a.pdf"
    archivo.write_bytes(b"x")

    assert storage.exists(archivo)
    assert storage.is_file(archivo)
    assert not storage.is_directory(archivo)

    assert storage.is_directory(tmp_path)
    assert not storage.is_file(tmp_path)
    assert not storage.exists(tmp_path / "fantasma.pdf")


def test_is_same_file_for_existing_paths(storage, tmp_path):
    archivo = tmp_path / "a.pdf"
    archivo.write_bytes(b"x")

    assert storage.is_same_file(archivo, tmp_path / "sub" / ".." / "a.pdf")
    assert not storage.is_same_file(archivo, tmp_path / "b.pdf")


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
    archivo = tmp_path / "a.pdf"
    archivo.write_bytes(b"x")

    with pytest.raises(InvalidOutputPathException, match="no existe"):
        storage.ensure_writable_directory(tmp_path / "fantasma")

    with pytest.raises(InvalidOutputPathException, match="no es un directorio"):
        storage.ensure_writable_directory(archivo)


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

    resultado = storage.unique_path(sub / "book_1-5.pdf")

    assert resultado.parent == sub
    assert resultado.name == "book_1-5_1.pdf"
