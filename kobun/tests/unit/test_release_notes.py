"""
El generador de notas vive en scripts/, que no es un paquete: se carga por ruta
para poder probar la clasificación, que es donde puede equivocarse.
"""
import importlib.util
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[3]


def _cargar_modulo():
    ruta = RAIZ / "scripts" / "release_notes.py"
    spec = importlib.util.spec_from_file_location("release_notes", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    return modulo


notas = _cargar_modulo()


def commit(asunto: str, hash_corto: str = "abc1234"):
    return notas.parse(hash_corto, asunto)


# =========================
# Parseo
# =========================


def test_parses_type_and_description():
    resultado = commit("feat: agrega selector de temas")

    assert resultado.type == "feat"
    assert resultado.text == "agrega selector de temas"
    assert resultado.scope is None
    assert not resultado.breaking


def test_parses_scope():
    resultado = commit("fix(ui): corrige el fondo del QLabel")

    assert resultado.scope == "ui"
    assert resultado.text == "corrige el fondo del QLabel"


def test_parses_breaking_marker():
    assert commit("feat!: cambia el formato del historial").breaking


def test_uppercase_type_is_normalised():
    """`Refactor:` y `refactor:` son el mismo tipo para quien lee las notas."""
    assert commit("Refactor: mueve AppTheme a shared").type == "refactor"


def test_commit_without_convention_keeps_its_subject():
    resultado = commit("Update README.md")

    assert resultado.type == notas.NO_TYPE
    assert resultado.text == "Update README.md"


# =========================
# Clasificación
# =========================


def test_sections_follow_the_declared_order():
    cuerpo = notas.build_notes(
        [
            commit("chore: sube pytest"),
            commit("fix: corrige el rango"),
            commit("feat: agrega el .deb"),
        ],
        tag="v0.2.0",
        previous="v0.1.0",
    )

    assert cuerpo.index("### New") < cuerpo.index("### Fixes") < cuerpo.index("Internal")


def test_breaking_goes_first_and_is_not_repeated_in_its_type():
    cuerpo = notas.build_notes(
        [commit("feat!: cambia el formato del historial"), commit("feat: agrega el .deb")],
        tag="v0.2.0",
        previous="v0.1.0",
    )

    assert cuerpo.index(notas.BREAKING_TITLE) < cuerpo.index("### New")
    assert cuerpo.count("cambia el formato del historial") == 1


def test_unknown_type_does_not_disappear():
    """
    Un tipo que no está en ninguna sección igual es un cambio: se publica en
    "Other changes" antes que quedar fuera de las notas sin que nadie lo note.
    """
    cuerpo = notas.build_notes([commit("wip: algo a medio hacer")], tag="v0.2.0", previous="v0.1.0")

    assert "### Other changes" in cuerpo
    assert "algo a medio hacer" in cuerpo


def test_internal_changes_are_folded():
    cuerpo = notas.build_notes(
        [commit("refactor: separa el resolvedor"), commit("ci: agrega la matriz")],
        tag="v0.2.0",
        previous="v0.1.0",
    )

    assert "<details>" in cuerpo
    assert "<summary>Internal (2)</summary>" in cuerpo


def test_does_not_repeat_the_same_change():
    """Los rebases y cherry-picks duplican asuntos; en las notas se leen mal."""
    cuerpo = notas.build_notes(
        [commit("feat: agrega el .deb", "aaa1111"), commit("feat: agrega el .deb", "bbb2222")],
        tag="v0.2.0",
        previous="v0.1.0",
    )

    assert cuerpo.count("agrega el .deb") == 1


def test_scope_is_highlighted_and_the_hash_follows():
    cuerpo = notas.build_notes(
        [commit("fix(ui): corrige el fondo", "abc1234")], tag="v0.2.0", previous="v0.1.0"
    )

    assert "- **ui**: corrige el fondo (abc1234)" in cuerpo


# =========================
# Documento completo
# =========================


def test_includes_the_install_instructions():
    cuerpo = notas.build_notes([commit("feat: algo")], tag="v0.2.0", previous="v0.1.0")

    assert "## Install" in cuerpo
    assert "sudo apt install" in cuerpo
    assert "kobun.exe" in cuerpo


def test_comparison_link_between_tags():
    cuerpo = notas.build_notes(
        [commit("feat: algo")], tag="v0.2.0", previous="v0.1.0", slug="IgnacioBarraza/kobun_pdf_splitter"
    )

    assert "compare/v0.1.0...v0.2.0" in cuerpo


def test_first_release_links_to_the_commit_list():
    cuerpo = notas.build_notes(
        [commit("feat: algo")], tag="v0.1.0", previous=None, slug="IgnacioBarraza/kobun_pdf_splitter"
    )

    assert "commits/v0.1.0" in cuerpo
    assert "First published version." in cuerpo


def test_no_commits_says_so_instead_of_leaving_the_section_empty():
    cuerpo = notas.build_notes([], tag="v0.2.0", previous="v0.1.0")

    assert "No changes recorded since v0.1.0." in cuerpo


# =========================
# Versiones y prereleases
# =========================


def test_the_tag_version_keeps_the_prerelease_suffix():
    """
    semantic-release escribe el sufijo en el paquete, así que la comparación es
    exacta: un `0.2.0` de paquete con un tag `v0.2.0-alpha.1` es un error.
    """
    assert notas.version_of_tag("v0.2.0-alpha.1") == "0.2.0-alpha.1"
    assert notas.version_of_tag("0.2.0") == "0.2.0"


def test_recognises_prereleases_by_their_suffix():
    assert notas.is_prerelease("v0.2.0-alpha.1")
    assert not notas.is_prerelease("v0.2.0")


def test_the_release_commit_is_not_a_change():
    """
    `chore(release): v0.2.0` lo escribe semantic-release al versionar; listarlo
    haría que cada release contara su propia publicación como novedad.
    """
    assert notas.is_release_commit(commit("chore(release): v0.2.0 [skip ci]"))
    assert not notas.is_release_commit(commit("chore: sube pytest"))


def test_a_prerelease_warns_before_the_install_block():
    cuerpo = notas.build_notes([commit("feat: algo")], tag="v0.2.0-alpha.1", previous="v0.1.0")

    assert cuerpo.index("Test build") < cuerpo.index("## Install")


def test_a_definitive_version_carries_no_warning():
    cuerpo = notas.build_notes([commit("feat: algo")], tag="v0.2.0", previous="v0.1.0")

    assert "Test build" not in cuerpo


def test_the_tag_has_to_match_the_package_version():
    """
    La versión se muestra dentro de la app: si el tag y el paquete no coinciden,
    lo descargado miente sobre qué versión es.
    """
    notas.check_version(f"v{notas.package_version()}")

    with pytest.raises(SystemExit, match="does not match"):
        notas.check_version("v99.0.0")


def test_a_nonexistent_revision_fails_with_a_message_and_not_a_traceback():
    with pytest.raises(SystemExit, match="does not exist in this repository"):
        notas.check_revision("v999.no-existe")
