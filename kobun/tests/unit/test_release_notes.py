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
    return notas.parsear(hash_corto, asunto)


# =========================
# Parseo
# =========================


def test_parsea_tipo_y_descripcion():
    resultado = commit("feat: agrega selector de temas")

    assert resultado.tipo == "feat"
    assert resultado.texto == "agrega selector de temas"
    assert resultado.ambito is None
    assert not resultado.rotura


def test_parsea_ambito():
    resultado = commit("fix(ui): corrige el fondo del QLabel")

    assert resultado.ambito == "ui"
    assert resultado.texto == "corrige el fondo del QLabel"


def test_parsea_marca_de_rotura():
    assert commit("feat!: cambia el formato del historial").rotura


def test_tipo_en_mayusculas_se_normaliza():
    """`Refactor:` y `refactor:` son el mismo tipo para quien lee las notas."""
    assert commit("Refactor: mueve AppTheme a shared").tipo == "refactor"


def test_commit_sin_convencion_conserva_el_asunto():
    resultado = commit("Update README.md")

    assert resultado.tipo == notas.SIN_TIPO
    assert resultado.texto == "Update README.md"


# =========================
# Clasificación
# =========================


def test_secciones_respetan_el_orden_declarado():
    cuerpo = notas.construir_notas(
        [
            commit("chore: sube pytest"),
            commit("fix: corrige el rango"),
            commit("feat: agrega el .deb"),
        ],
        tag="v0.2.0",
        anterior="v0.1.0",
    )

    assert cuerpo.index("### Nuevo") < cuerpo.index("### Correcciones") < cuerpo.index("Interno")


def test_rotura_va_primero_y_no_se_repite_en_su_tipo():
    cuerpo = notas.construir_notas(
        [commit("feat!: cambia el formato del historial"), commit("feat: agrega el .deb")],
        tag="v0.2.0",
        anterior="v0.1.0",
    )

    assert cuerpo.index(notas.TITULO_ROTURA) < cuerpo.index("### Nuevo")
    assert cuerpo.count("cambia el formato del historial") == 1


def test_tipo_desconocido_no_desaparece():
    """
    Un tipo que no está en ninguna sección igual es un cambio: se publica en
    "Otros cambios" antes que quedar fuera de las notas sin que nadie lo note.
    """
    cuerpo = notas.construir_notas([commit("wip: algo a medio hacer")], tag="v0.2.0", anterior="v0.1.0")

    assert "### Otros cambios" in cuerpo
    assert "algo a medio hacer" in cuerpo


def test_los_internos_quedan_plegados():
    cuerpo = notas.construir_notas(
        [commit("refactor: separa el resolvedor"), commit("ci: agrega la matriz")],
        tag="v0.2.0",
        anterior="v0.1.0",
    )

    assert "<details>" in cuerpo
    assert "<summary>Interno (2)</summary>" in cuerpo


def test_no_repite_el_mismo_cambio():
    """Los rebases y cherry-picks duplican asuntos; en las notas se leen mal."""
    cuerpo = notas.construir_notas(
        [commit("feat: agrega el .deb", "aaa1111"), commit("feat: agrega el .deb", "bbb2222")],
        tag="v0.2.0",
        anterior="v0.1.0",
    )

    assert cuerpo.count("agrega el .deb") == 1


def test_el_ambito_se_destaca_y_el_hash_acompana():
    cuerpo = notas.construir_notas(
        [commit("fix(ui): corrige el fondo", "abc1234")], tag="v0.2.0", anterior="v0.1.0"
    )

    assert "- **ui**: corrige el fondo (abc1234)" in cuerpo


# =========================
# Documento completo
# =========================


def test_incluye_las_instrucciones_de_instalacion():
    cuerpo = notas.construir_notas([commit("feat: algo")], tag="v0.2.0", anterior="v0.1.0")

    assert "## Instalación" in cuerpo
    assert "sudo apt install" in cuerpo
    assert "kobun.exe" in cuerpo


def test_enlace_de_comparacion_entre_tags():
    cuerpo = notas.construir_notas(
        [commit("feat: algo")], tag="v0.2.0", anterior="v0.1.0", slug="IgnacioBarraza/kobun_pdf_splitter"
    )

    assert "compare/v0.1.0...v0.2.0" in cuerpo


def test_primera_release_enlaza_a_la_lista_de_commits():
    cuerpo = notas.construir_notas(
        [commit("feat: algo")], tag="v0.1.0", anterior=None, slug="IgnacioBarraza/kobun_pdf_splitter"
    )

    assert "commits/v0.1.0" in cuerpo
    assert "Primera versión publicada." in cuerpo


def test_sin_commits_lo_dice_en_vez_de_dejar_la_seccion_vacia():
    cuerpo = notas.construir_notas([], tag="v0.2.0", anterior="v0.1.0")

    assert "Sin cambios registrados desde v0.1.0." in cuerpo


# =========================
# Coherencia de la versión
# =========================


def test_la_version_del_tag_conserva_el_sufijo_de_prerelease():
    """
    semantic-release escribe el sufijo en el paquete, así que la comparación es
    exacta: un `0.2.0` de paquete con un tag `v0.2.0-alpha.1` es un error.
    """
    assert notas.version_del_tag("v0.2.0-alpha.1") == "0.2.0-alpha.1"
    assert notas.version_del_tag("0.2.0") == "0.2.0"


def test_reconoce_las_prereleases_por_el_sufijo():
    assert notas.es_prerelease("v0.2.0-alpha.1")
    assert not notas.es_prerelease("v0.2.0")


def test_el_commit_de_la_propia_release_no_es_un_cambio():
    """
    `chore(release): v0.2.0` lo escribe semantic-release al versionar; listarlo
    haría que cada release contara su propia publicación como novedad.
    """
    assert notas.es_commit_de_release(commit("chore(release): v0.2.0 [skip ci]"))
    assert not notas.es_commit_de_release(commit("chore: sube pytest"))


def test_una_prerelease_avisa_antes_del_bloque_de_instalacion():
    cuerpo = notas.construir_notas([commit("feat: algo")], tag="v0.2.0-alpha.1", anterior="v0.1.0")

    assert cuerpo.index("Versión de prueba") < cuerpo.index("## Instalación")


def test_una_version_definitiva_no_lleva_el_aviso():
    cuerpo = notas.construir_notas([commit("feat: algo")], tag="v0.2.0", anterior="v0.1.0")

    assert "Versión de prueba" not in cuerpo


def test_el_tag_tiene_que_coincidir_con_la_version_del_paquete():
    """
    La versión se muestra dentro de la app: si el tag y el paquete no coinciden,
    lo descargado miente sobre qué versión es.
    """
    notas.verificar_version(f"v{notas.version_del_paquete()}")

    with pytest.raises(SystemExit, match="no coincide"):
        notas.verificar_version("v99.0.0")


def test_una_revision_inexistente_falla_con_un_mensaje_y_no_un_traceback():
    with pytest.raises(SystemExit, match="no existe en este repositorio"):
        notas.verificar_revision("v999.no-existe")
