# Kobun – PDF Desktop Utility

## 📖 Overview

**Kobun** is a desktop utility for splitting PDF files by page ranges, designed with a clean architecture and a strong separation between domain logic and UI concerns.

The application enables users to reorganize large PDF documents — such as academic books, technical manuals, or research material — into smaller, well-defined sections.

The project emphasizes:

- Clear domain modeling
- Framework-independent business rules
- Maintainable layered architecture
- Modern Qt-based desktop interface

---

## ✨ Features

### Splitting

- Extract page ranges, including discontinuous selections: `1-5,10-15,20`
- Overlapping or adjacent ranges are merged automatically — no duplicate pages
- Page indices are 1-based and inclusive, as printed in the document
- Output metadata derived from the source document, traceable back to it
- PDF processing powered by **PyMuPDF**

### Choosing where it lands

- Suggested output filename: `book.pdf` + `1-5,10-15` → `book_1-5_10-15.pdf`,
  sanitized for Windows/macOS/Linux
- The destination field asks for a filename; the folder is shown separately
- Output never overwrites silently — `OverwritePolicy` (`FAIL` / `OVERWRITE` /
  `RENAME`) — and never writes over the source file

### Reading the input safely

- Rejects unreadable input before processing: missing files, directories,
  empty files, non-PDFs, and password-protected PDFs
- Strict domain validation for invalid page ranges
- Explicit domain-level exceptions — PyMuPDF errors never reach the caller

### Interface

- Desktop interface built with **PySide6 (Qt for Python)**
- Drag & drop, or pick a file from the system dialog
- Long operations run on a worker thread, so the window never freezes
- Expected errors are reported as warnings; unexpected ones show a generic
  message and keep the technical detail for reporting
- **10 themes**, 5 light and 5 dark, most of them built around a Japanese
  palette (washi, indigo, matcha, ink, bamboo, violet…). The choice persists
  between sessions

### Export history

- Persistent history of the last 50 exports, stored per-OS in the user's data
  directory
- Entries whose file was moved or deleted are flagged, not dropped
- Open an exported PDF with the system viewer, straight from the list

---

## 🧱 Architecture

Kobun follows a layered structure inspired by Domain-Driven Design (DDD):

```
kobun/
│
├── domain/         # Core business rules and value objects
├── application/    # Use cases, DTOs and port interfaces
├── infrastructure/ # PDF engine, filesystem and persistence (PyMuPDF, JSON)
├── presentation/   # Qt UI (PySide6) and viewmodels
├── shared/         # Cross-cutting concerns (themes, settings, icons)
└── tests/          # unit/ (no dependencies) and integration/ (real PDFs, real window)

assets/             # Source artwork, not shipped with the package
docs/               # changelog.md, written by semantic-release on every release
scripts/            # Build, packaging, release and desktop integration helpers
```

### Architectural Principles

- Immutable Value Objects
- Explicit domain exceptions
- No framework leakage into the domain layer
- Deterministic validation of page ranges
- Clear dependency direction (outer layers depend on inner layers)
- **Page indices are 1-based everywhere** — from `PageRange` up to the UI. The
  translation to PyMuPDF's 0-based API happens only inside `PdfEngineAdapter`.
- The UI knows no use cases: the window talks to a viewmodel, and the
  viewmodel is the only thing that touches the application layer.

---

## 🛠 Requirements

- Python **3.10+**
- pip

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

That installs the project in editable mode with its development extras.
`requirements.txt` only points at `pyproject.toml`, which is the single source
of truth for dependencies.

Once installed, the `kobun` command is available:

```bash
kobun                    # opens the window
kobun path/to/book.pdf   # opens it with that document loaded
```

---

## 🚀 Running the Application

```bash
kobun                    # if the project is installed
./.venv/bin/python main.py   # straight from the source tree
```

Both accept a PDF as an argument, which is also how the desktop passes the file
when Kobun is chosen from "Open with".

### Desktop integration on Linux (optional)

On Wayland the compositor does not read the icon from the window: it matches
the application to a `.desktop` file through its app id. Without that file the
dock shows a generic Python icon.

```bash
./.venv/bin/python scripts/install_desktop_entry.py
```

This installs the icons into `~/.local/share/icons/hicolor` and the entry into
`~/.local/share/applications`, with no root required. Kobun then appears in the
application menu too. Use `--uninstall` to undo it.

---

## 📦 Building an executable

```bash
pip install -e .[build]
python scripts/build_app.py            # single file, easiest to distribute
python scripts/build_app.py --onedir    # a folder, starts faster
```

The recipe lives in [`packaging/kobun.spec`](packaging/kobun.spec) and is shared
by both platforms. **PyInstaller does not cross-compile**: the Linux binary must
be built on Linux and the Windows `.exe` on Windows (or in CI).

A build that succeeds is not a build that works — a Qt module excluded too
aggressively only fails at startup. Always launch the result before shipping it.

| | Linux | Windows |
|---|---|---|
| Output | `dist/kobun` | `dist/kobun.exe` |
| Size | ~93 MB (one file) | similar |
| Installer | `.deb` (see below) | Inno Setup (see below) |
| Icon | resolved by the desktop from the `.desktop` entry | embedded in the `.exe` |
| Console window | n/a | none (`console=False`) |

Released files are named `kobun`, `kobun.exe` and `kobun_<version>_amd64.deb`.
The version is not in the first two names because the app shows it in its own
sidebar; the `.deb` keeps the Debian convention because tooling expects it.

On Linux, point the desktop entry at the built binary instead of the
development environment:

```bash
python scripts/install_desktop_entry.py --exec dist/kobun
```

### Linux package

A bare executable is not a usable distribution format on Linux: modern file
managers refuse to launch binaries on double-click, and downloading one loses
its executable bit. The `.deb` is the Linux counterpart of the Windows
installer — it puts the binary in `/usr/bin`, registers the `.desktop` entry and
the icons, and shows up in the application menu.

```bash
python scripts/build_app.py
python scripts/build_deb.py
sudo apt install ./dist/kobun_*_amd64.deb
```

Its dependencies were not guessed: they come from walking the `NEEDED` entries
of every library in the Qt bundle and mapping what is missing to packages.

### Getting the Windows `.exe` without a Windows machine

[`.github/workflows/build.yml`](.github/workflows/build.yml) runs the test suite,
then builds both binaries on their own runners and uploads them as artifacts.
Merging into `develop` or `main` also publishes them as a release — see
[Publishing a release](#publishing-a-release).

### Windows installer

The `.exe` is **portable**: it runs on double-click, with no installation. What
it does not give you is a Start menu shortcut, a PDF association or an entry in
Add/Remove Programs. That is what [`packaging/kobun.iss`](packaging/kobun.iss)
adds, via Inno Setup:

```bat
python scripts\build_app.py
iscc packaging\kobun.iss
```

It installs per-user, so no UAC prompt, and it registers Kobun as an *option*
for PDFs rather than stealing the default association from whatever viewer is
already installed.

Note that an unsigned executable downloaded from the internet triggers a
SmartScreen warning on first run. Removing it requires a code-signing
certificate.

### Publishing a release

Nothing is tagged by hand. The version comes from the commits, through
[python-semantic-release](https://python-semantic-release.readthedocs.io/),
configured under `[tool.semantic_release]` in
[`pyproject.toml`](pyproject.toml). Push to a release branch and the pipeline
decides whether there is a version to publish, and which one:

| Commit prefix | Effect on the version |
|---|---|
| `feat:` | minor — `0.1.0` → `0.2.0` |
| `fix:` `perf:` | patch — `0.1.0` → `0.1.1` |
| `feat!:` or `BREAKING CHANGE:` | minor while below 1.0.0 (`major_on_zero = false`) |
| `docs:` `chore:` `ci:` `refactor:` `test:` `style:` `build:` | nothing — no release |

Two branches release:

| Branch | Version | GitHub release |
|---|---|---|
| `develop` | `0.2.0-alpha.1`, `.2`, … | marked **pre-release** |
| `main` | `0.2.0` | the definitive one |

So a merge into `develop` gives you installable binaries to try before the
version is final, and the merge from `develop` into `main` turns the accumulated
alphas into the stable release.

When there is something to publish, the pipeline bumps `__version__` in
[`kobun/__init__.py`](kobun/__init__.py), inserts the entry into
[`docs/changelog.md`](docs/changelog.md), commits that as
`chore(release): vX.Y.Z [skip ci]`, tags it, creates the release, and only then
builds the binaries from the tag and attaches them. Nothing to publish means
nothing happens — no empty release, no tag.

**Preview what a release would say**, before pushing anything:

```bash
pip install -e .[release]
semantic-release version --print          # the next version, or the current one if none
python3 scripts/release_notes.py v0.2.0   # the release body, once the tag exists
```

#### Two documents, on purpose

[`docs/changelog.md`](docs/changelog.md) is the **record**: every version, in
semantic-release's own format, written by the tool.

The GitHub release body is the **shop window**, written by
[`scripts/release_notes.py`](scripts/release_notes.py): it leads with the
install instructions, groups changes in Spanish, folds `refactor:`/`chore:`/`ci:`
away in a `<details>`, and warns when the download is a pre-release.

It also fixes something the record cannot: semantic-release attributes each
commit to the tag that first published it, so a stable release that follows a
string of alphas has **nothing left of its own** and its notes come out empty.
The generator compares a definitive version against the last definitive
version — not against the last alpha — so the release that people actually
download lists everything that changed since the previous one they had.

Commits that do not follow the convention are never dropped from the notes: they
land in *Otros cambios*. They just do not move the version.

---

## 🧪 Tests

```bash
pytest                        # everything (testpaths is configured)
pytest kobun/tests/unit       # pure domain, no dependencies
```

The `unit/` suite runs with nothing but pytest installed. The `integration/`
suite generates real PDFs with PyMuPDF and drives the real Qt window in
offscreen mode, checking that exactly the requested pages come out; it skips
itself when PyMuPDF or PySide6 are missing.

---

## 📂 Example Workflow

1. Drop `book.pdf` on the window
2. Enter a page selection: `25-40`, or `1-5,10-15,20` for several sections at once
3. Click **DIVIDIR PDF**
4. Receive a PDF with exactly those pages, in that order

From code:

```python
document = load_use_case.execute(Path("book.pdf"))       # validates the source
selection = PageSelection.parse("1-5,10-15")

response = split_use_case.execute(SplitPdfRequest(
    input_path=document.storage_path,
    selection=selection,
    output_path=None,                                    # suggested name
    policy=OverwritePolicy.RENAME,                       # do not fail if taken
))

record_use_case.execute(response)                        # add it to the history
```

---

[//]: # (## 🌐 Landing Page)

[//]: # ()
[//]: # (For documentation, roadmap updates, and project vision:)

[//]: # ()
[//]: # (👉 **Visit the official Kobun landing page:**  )

[//]: # (https://your-landing-page-url.com)

[//]: # (---)

## 🛣 Roadmap

- [x] Multiple range support (e.g., `1-5,10-15`)
- [x] Automated tests for domain layer
- [x] Output path selection with overwrite policy
- [x] Export history
- [x] Qt UI wired to the use cases
- [x] Light / dark theme system
- [ ] Page preview before splitting
- [ ] Batch splitting
- [ ] CLI version
- [x] Installable package with a `kobun` entry point
- [ ] Cross-platform packaging (Windows / macOS / Linux)
- [ ] Installer distribution

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Follow clean code and architectural boundaries
4. Submit a pull request with a clear technical description

Please ensure:

- Domain logic remains UI-agnostic
- New features include validation and explicit error handling
- Layer boundaries are respected
- The `unit/` suite still runs without PyMuPDF or PySide6 installed

---

## 📄 License

Released under the MIT License.  
See `LICENSE` for details.
