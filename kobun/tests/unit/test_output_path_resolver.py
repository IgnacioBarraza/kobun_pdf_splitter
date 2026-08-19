import os

import pytest

from kobun.application.services.output_path_resolver import OutputPathResolver
from kobun.domain.pdf.exceptions.invalid_output_path_exception import InvalidOutputPathException
from kobun.domain.pdf.value_objects.overwrite_policy import OverwritePolicy
from kobun.infrastructure.filesystem.local_file_storage import LocalFileStorage

DEFAULT_NAME = "book_1-5.pdf"


@pytest.fixture
def resolver():
    return OutputPathResolver(LocalFileStorage())


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "book.pdf"
    path.write_bytes(b"%PDF-1.7 source")
    return path


def test_explicit_pdf_path_is_used_as_is(resolver, source, tmp_path):
    requested = tmp_path / "mi_export.pdf"

    assert resolver.resolve(requested, source, DEFAULT_NAME) == requested


def test_directory_gets_the_default_filename_appended(resolver, source, tmp_path):
    directory = tmp_path / "exports"
    directory.mkdir()

    assert resolver.resolve(directory, source, DEFAULT_NAME) == directory / DEFAULT_NAME


def test_uppercase_pdf_suffix_is_accepted(resolver, source, tmp_path):
    requested = tmp_path / "EXPORT.PDF"

    assert resolver.resolve(requested, source, DEFAULT_NAME) == requested


def test_path_without_pdf_suffix_is_rejected(resolver, source, tmp_path):
    with pytest.raises(InvalidOutputPathException, match="debe ser un directorio existente"):
        resolver.resolve(tmp_path / "export", source, DEFAULT_NAME)


def test_wrong_suffix_is_rejected(resolver, source, tmp_path):
    with pytest.raises(InvalidOutputPathException, match="terminar en"):
        resolver.resolve(tmp_path / "export.docx", source, DEFAULT_NAME)


def test_writing_over_the_source_file_is_rejected(resolver, source):
    with pytest.raises(InvalidOutputPathException, match="mismo archivo de origen"):
        resolver.resolve(source, source, DEFAULT_NAME)


def test_writing_over_the_source_via_relative_path_is_rejected(resolver, source, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(InvalidOutputPathException, match="mismo archivo de origen"):
        resolver.resolve(tmp_path / "sub" / ".." / "book.pdf", source, DEFAULT_NAME)


def test_missing_output_directory_is_rejected(resolver, source, tmp_path):
    with pytest.raises(InvalidOutputPathException, match="no existe"):
        resolver.resolve(tmp_path / "nope" / "out.pdf", source, DEFAULT_NAME)


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignora los permisos de escritura")
def test_unwritable_output_directory_is_rejected(resolver, source, tmp_path):
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o500)

    try:
        with pytest.raises(InvalidOutputPathException, match="permiso de escritura"):
            resolver.resolve(locked / "out.pdf", source, DEFAULT_NAME)
    finally:
        locked.chmod(0o700)


def test_existing_file_fails_by_default(resolver, source, tmp_path):
    existing = tmp_path / "out.pdf"
    existing.write_bytes(b"previo")

    with pytest.raises(InvalidOutputPathException, match="ya existe"):
        resolver.resolve(existing, source, DEFAULT_NAME)


def test_existing_file_is_kept_with_overwrite_policy(resolver, source, tmp_path):
    existing = tmp_path / "out.pdf"
    existing.write_bytes(b"previo")

    resolved = resolver.resolve(existing, source, DEFAULT_NAME, OverwritePolicy.OVERWRITE)

    assert resolved == existing


def test_existing_file_gets_a_free_name_with_rename_policy(resolver, source, tmp_path):
    (tmp_path / "out.pdf").write_bytes(b"previo")
    (tmp_path / "out_1.pdf").write_bytes(b"previo")

    resolved = resolver.resolve(tmp_path / "out.pdf", source, DEFAULT_NAME, OverwritePolicy.RENAME)

    assert resolved == tmp_path / "out_2.pdf"


def test_rename_policy_on_a_free_path_changes_nothing(resolver, source, tmp_path):
    requested = tmp_path / "libre.pdf"

    assert resolver.resolve(requested, source, DEFAULT_NAME, OverwritePolicy.RENAME) == requested


def test_directory_colliding_with_the_default_filename_is_rejected(resolver, source, tmp_path):
    directory = tmp_path / "exports"
    directory.mkdir()
    (directory / DEFAULT_NAME).mkdir()

    with pytest.raises(InvalidOutputPathException, match="Ya existe un directorio"):
        resolver.resolve(directory, source, DEFAULT_NAME)


def test_policy_accepts_its_plain_string_value(resolver, source, tmp_path):
    """
    Regresión: Qt guarda el enum del combo como str plano, así que el resolver
    debe reconocer "rename" igual que OverwritePolicy.RENAME. Con comparación
    por identidad, elegir esa política desde la UI no hacía nada.
    """
    (tmp_path / "out.pdf").write_bytes(b"previo")

    resuelto = resolver.resolve(tmp_path / "out.pdf", source, DEFAULT_NAME, "rename")

    assert resuelto == tmp_path / "out_1.pdf"
