#!/usr/bin/env python3
"""
Redacta las notas de una release a partir de los commits desde el tag anterior.

    python3 scripts/release_notes.py v0.2.0
    python3 scripts/release_notes.py v0.2.0 --salida notas.md

Los commits del proyecto siguen la convención `tipo: descripción`, así que las
secciones se pueden armar solas y lo único que se mantiene a mano es el bloque
de instalación, que no depende de los cambios.

Estas notas son la vitrina de la release —lo que ve quien entra a descargar la
app—; el registro histórico lo escribe semantic-release en docs/changelog.md.
Por eso son dos formatos distintos: uno agrupa para leer, el otro archiva.

No usa ninguna dependencia: tiene que poder correr en el runner de la release
sin instalar el proyecto.
"""
import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

RAIZ = Path(__file__).resolve().parent.parent

# Separador de unidad: no puede aparecer en el asunto de un commit, a diferencia
# de cualquier carácter imprimible que se nos ocurra.
SEPARADOR = "\x1f"

# Marca para los commits que no siguen la convención.
SIN_TIPO = "*"

OTROS = "Otros cambios"

# Cambios que no le dicen nada a quien sólo quiere usar la app: se publican,
# pero plegados.
TIPOS_INTERNOS = (
    "refactor",
    "chore",
    "docs",
    "doc",
    "test",
    "tests",
    "build",
    "ci",
    "style",
    "revert",
)

# (título, tipos que agrupa, plegada). El orden es el de aparición en las notas.
SECCIONES: Tuple[Tuple[str, Tuple[str, ...], bool], ...] = (
    ("Nuevo", ("feat",), False),
    ("Correcciones", ("fix",), False),
    ("Rendimiento", ("perf",), False),
    (OTROS, (SIN_TIPO,), False),
    ("Interno", TIPOS_INTERNOS, True),
)

TITULO_ROTURA = "Cambios que rompen compatibilidad"

PATRON_COMMIT = re.compile(
    r"^(?P<tipo>[A-Za-z]+)(?:\((?P<ambito>[^)]*)\))?(?P<rotura>!)?:\s*(?P<texto>.+)$"
)

PATRON_VERSION = re.compile(r'__version__\s*=\s*["\']([^"\']+)["\']')

# El commit que escribe semantic-release al versionar no es un cambio del
# proyecto: aparecería como "chore(release): v0.2.0" en medio de las notas.
TIPO_DE_RELEASE = ("chore", "release")

AVISO_PRERELEASE = (
    "> **Versión de prueba.** Sale automáticamente de `develop` para poder probar "
    "los cambios antes de que salgan como versión definitiva. Puede tener fallas; "
    "si buscás la última versión estable, andá a "
    "[releases](https://github.com/IgnacioBarraza/kobun_pdf_splitter/releases/latest)."
)

INSTALACION = """## Instalación

### Windows

`kobun.exe` es portable: se descarga y se abre, no se instala.

### Linux

**Recomendado**: el `.deb`, que instala la app en el menú de aplicaciones con su
icono.

```
sudo apt install ./kobun_*_amd64.deb
```

El binario suelto `kobun` sirve para otras distribuciones, pero tené en cuenta
dos cosas: hay que darle permiso con `chmod +x` (el ZIP de descarga no lo
preserva) y **los exploradores de archivos modernos no lanzan binarios con doble
clic**, así que hay que ejecutarlo desde una terminal."""


class ErrorDeGit(RuntimeError):
    pass


@dataclass(frozen=True)
class Commit:
    hash: str
    tipo: str
    ambito: Optional[str]
    texto: str
    rotura: bool


# =========================
# Lectura de la historia
# =========================


def _git(*argumentos: str) -> str:
    resultado = subprocess.run(
        ("git", "-C", str(RAIZ), *argumentos),
        capture_output=True,
        text=True,
    )

    if resultado.returncode != 0:
        raise ErrorDeGit(resultado.stderr.strip() or f"git {' '.join(argumentos)} falló")

    return resultado.stdout.strip()


def tag_de_head() -> str:
    """El tag que apunta exactamente a HEAD, para no tener que escribirlo."""
    try:
        return _git("describe", "--tags", "--exact-match", "HEAD")
    except ErrorDeGit:
        raise SystemExit(
            "HEAD no está etiquetado: pasá el tag como argumento.\n"
            "    python3 scripts/release_notes.py v0.2.0"
        )


def es_prerelease(tag: str) -> bool:
    """`v0.2.0-alpha.1` sí, `v0.2.0` no: el guión sólo aparece en el sufijo."""
    return "-" in tag.lstrip("vV")


def tag_anterior(tag: str, solo_estables: bool = False) -> Optional[str]:
    """
    El tag anterior alcanzable desde `tag`, o None si es la primera release.

    Se busca desde el padre del tag y no desde el tag mismo, porque describe
    devolvería el propio tag.

    `solo_estables` es lo que hace que una versión definitiva no salga vacía:
    los cambios ya se publicaron en las prereleases, así que si el tag anterior
    fuera el último alpha no quedaría nada que contar. Se compara contra el
    último estable y la nota cuenta todo lo que pasó desde entonces.
    """
    argumentos = ["describe", "--tags", "--abbrev=0"]
    if solo_estables:
        argumentos.append("--exclude=*-*")

    try:
        return _git(*argumentos, f"{tag}^")
    except ErrorDeGit:
        return None


def verificar_revision(revision: str) -> None:
    """
    Un tag inexistente es el error más fácil de cometer —escribir el tag antes
    de crearlo— y sin esto se manifiesta como un traceback de git.
    """
    try:
        _git("rev-parse", "--verify", "--quiet", f"{revision}^{{commit}}")
    except ErrorDeGit:
        raise SystemExit(
            f"{revision} no existe en este repositorio.\n"
            "Si es un tag nuevo, crealo antes:  git tag v0.2.0"
        )


def leer_commits(tag: str, desde: Optional[str]) -> List[Commit]:
    rango = f"{desde}..{tag}" if desde else tag

    # Sin merges: "Merge pull request #1 from ..." no es un cambio, es cómo
    # entró el cambio.
    salida = _git("log", rango, "--no-merges", f"--pretty=%h{SEPARADOR}%s")

    commits = [parsear(*linea.split(SEPARADOR, 1)) for linea in salida.splitlines() if linea.strip()]

    return [commit for commit in commits if not es_commit_de_release(commit)]


def slug_del_repo() -> Optional[str]:
    """`usuario/repo`, para armar el enlace de comparación."""
    del_entorno = os.environ.get("GITHUB_REPOSITORY")
    if del_entorno:
        return del_entorno

    try:
        url = _git("remote", "get-url", "origin")
    except ErrorDeGit:
        return None

    coincidencia = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?$", url)

    return coincidencia.group(1) if coincidencia else None


# =========================
# Clasificación
# =========================


def parsear(hash_corto: str, asunto: str) -> Commit:
    coincidencia = PATRON_COMMIT.match(asunto.strip())

    if coincidencia is None:
        return Commit(hash=hash_corto, tipo=SIN_TIPO, ambito=None, texto=asunto.strip(), rotura=False)

    ambito = coincidencia.group("ambito")

    return Commit(
        hash=hash_corto,
        tipo=coincidencia.group("tipo").lower(),
        ambito=ambito.strip() if ambito else None,
        texto=coincidencia.group("texto").strip(),
        rotura=coincidencia.group("rotura") is not None,
    )


def es_commit_de_release(commit: Commit) -> bool:
    """El commit que versiona no es un cambio: lo escribe la propia release."""
    return (commit.tipo, commit.ambito) == TIPO_DE_RELEASE


def _titulo_de(commit: Commit) -> str:
    if commit.rotura:
        return TITULO_ROTURA

    for titulo, tipos, _ in SECCIONES:
        if commit.tipo in tipos:
            return titulo

    # Un tipo que no conocemos igual es un cambio: cae en "Otros cambios" antes
    # que desaparecer de las notas.
    return OTROS


def agrupar(commits: Sequence[Commit]) -> Dict[str, List[Commit]]:
    """
    Agrupa por sección, sin repetir textos.

    Los duplicados aparecen solos con rebases y cherry-picks; en las notas se
    leen como si el cambio se hubiera hecho dos veces.
    """
    grupos: Dict[str, List[Commit]] = {}
    vistos = set()

    for commit in commits:
        clave = (commit.tipo, commit.ambito, commit.texto)
        if clave in vistos:
            continue

        vistos.add(clave)
        grupos.setdefault(_titulo_de(commit), []).append(commit)

    return grupos


# =========================
# Redacción
# =========================


def _linea(commit: Commit) -> str:
    # El texto va tal cual lo escribió quien commiteó: capitalizarlo rompería
    # nombres como `pyproject.toml` u `open_in_default_app`.
    texto = f"**{commit.ambito}**: {commit.texto}" if commit.ambito else commit.texto

    # GitHub convierte el hash en enlace al commit por su cuenta.
    return f"- {texto} ({commit.hash})"


def _bloque(titulo: str, commits: Sequence[Commit], plegado: bool) -> str:
    lineas = "\n".join(_linea(commit) for commit in commits)

    if plegado:
        return f"<details>\n<summary>{titulo} ({len(commits)})</summary>\n\n{lineas}\n\n</details>"

    return f"### {titulo}\n\n{lineas}"


def _orden_de_secciones() -> List[Tuple[str, bool]]:
    # Lo que rompe compatibilidad va primero: es lo que puede obligar a hacer
    # algo antes de actualizar.
    return [(TITULO_ROTURA, False)] + [(titulo, plegada) for titulo, _, plegada in SECCIONES]


def construir_notas(
    commits: Sequence[Commit],
    tag: str,
    anterior: Optional[str],
    slug: Optional[str] = None,
) -> str:
    # La instalación va arriba: la mayoría de quienes abren una release vienen a
    # descargar la app, no a leer el changelog. Antes va el aviso, si aplica:
    # quien descarga una alpha tiene que saberlo antes de bajar el binario.
    partes = [AVISO_PRERELEASE] if es_prerelease(tag) else []
    partes += [INSTALACION, "## Cambios"]

    if not commits:
        partes.append(f"Sin cambios registrados{f' desde {anterior}' if anterior else ''}.")
    else:
        if anterior is None:
            partes.append("Primera versión publicada.")

        grupos = agrupar(commits)

        for titulo, plegada in _orden_de_secciones():
            if titulo in grupos:
                partes.append(_bloque(titulo, grupos[titulo], plegada))

    enlace = _enlace_de_comparacion(tag, anterior, slug)
    if enlace:
        partes.append(enlace)

    return "\n\n".join(partes) + "\n"


def _enlace_de_comparacion(tag: str, anterior: Optional[str], slug: Optional[str]) -> Optional[str]:
    if not slug:
        return None

    base = f"https://github.com/{slug}"

    if anterior:
        return f"**Todos los cambios**: {base}/compare/{anterior}...{tag}"

    return f"**Todos los cambios**: {base}/commits/{tag}"


# =========================
# Coherencia de la versión
# =========================


def version_del_paquete() -> str:
    """
    Se lee el archivo en vez de importar el paquete: así el script sigue siendo
    stdlib puro y no depende de que kobun sea importable en el runner.
    """
    texto = (RAIZ / "kobun" / "__init__.py").read_text(encoding="utf-8")
    coincidencia = PATRON_VERSION.search(texto)

    if coincidencia is None:
        raise SystemExit("No se pudo leer __version__ de kobun/__init__.py")

    return coincidencia.group(1)


def version_del_tag(tag: str) -> str:
    """`v0.2.0-alpha.1` -> `0.2.0-alpha.1`: sólo se cae la `v` del formato."""
    return tag.lstrip("vV")


def verificar_version(tag: str) -> None:
    """
    El sufijo de prerelease se compara también: semantic-release escribe
    `0.2.0-alpha.1` en el paquete, así que la app dice exactamente lo mismo que
    el tag y cualquier diferencia es una desincronización real.
    """
    esperada = version_del_paquete()
    encontrada = version_del_tag(tag)

    if encontrada != esperada:
        raise SystemExit(
            f"El tag {tag} no coincide con la versión del paquete ({esperada}).\n"
            "La versión se muestra dentro de la app, así que publicar con este tag\n"
            f"haría que Kobun dijera v{esperada} siendo la release {tag}.\n"
            "Normalmente esto significa que el tag se creó a mano: los tags los\n"
            "crea semantic-release al versionar, y ahí los dos salen del mismo lugar."
        )


# =========================
# Entrada
# =========================


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", nargs="?", help="Tag de la release (por defecto, el que apunta a HEAD)")
    parser.add_argument("--desde", help="Tag o commit de referencia (por defecto, el tag anterior)")
    parser.add_argument("--salida", type=Path, help="Archivo donde escribir (por defecto, la salida estándar)")
    parser.add_argument(
        "--sin-verificar-version",
        action="store_true",
        help="No exigir que el tag coincida con kobun.__version__",
    )
    args = parser.parse_args(argv)

    tag = args.tag or tag_de_head()

    if not args.sin_verificar_version:
        verificar_version(tag)

    verificar_revision(tag)

    # Una versión definitiva se compara contra la última definitiva; una
    # prerelease, contra el tag inmediatamente anterior.
    anterior = args.desde or tag_anterior(tag, solo_estables=not es_prerelease(tag))
    if anterior:
        verificar_revision(anterior)

    try:
        commits = leer_commits(tag, anterior)
    except ErrorDeGit as error:
        raise SystemExit(f"git falló: {error}")

    notas = construir_notas(commits, tag, anterior, slug_del_repo())

    if args.salida:
        args.salida.write_text(notas, encoding="utf-8")
        print(f"{args.salida}: {len(commits)} commits desde {anterior or 'el inicio'}", file=sys.stderr)
    else:
        sys.stdout.write(notas)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
