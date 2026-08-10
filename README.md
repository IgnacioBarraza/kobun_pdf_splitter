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
scripts/            # Desktop integration helpers
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
