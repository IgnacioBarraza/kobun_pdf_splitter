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

> **Estado actual:** el dominio, la aplicación y la infraestructura están
> cerrados y cubiertos por tests. La interfaz Qt está en construcción: hoy el
> entry point es una CLI provisional que ejercita el mismo use case que usará
> la UI.

---

## ✨ Features

Ya disponibles (dominio + infraestructura):

- PDF processing powered by **PyMuPDF**
- Extract page ranges, including discontinuous selections: `1-5,10-15,20`
- Overlapping or adjacent ranges are merged automatically — no duplicate pages
- Output metadata derived from the source document, traceable back to it
- Strict domain validation for invalid page ranges
- Explicit domain-level exceptions

En construcción (capa de presentación):

- Desktop interface built with **PySide6 (Qt for Python)**
- Select any local PDF file from the UI
- Open the exported PDF directly from the application
- Recently exported files history

---

## 🧱 Architecture

Kobun follows a layered structure inspired by Domain-Driven Design (DDD):

```
kobun/
│
├── domain/         # Core business rules and value objects
├── application/    # Use cases and orchestration
├── infrastructure/ # PDF and file system integrations (PyMuPDF)
├── presentation/   # Qt UI (PySide6)
├── shared/         # Cross-cutting concerns (themes, settings)
└── tests/          # unit/ (pure domain) and integration/ (real PDFs)
```

### Architectural Principles

- Immutable Value Objects
- Explicit domain exceptions
- No framework leakage into the domain layer
- Deterministic validation of page ranges
- Clear dependency direction (outer layers depend on inner layers)
- **Page indices are 1-based everywhere** — from `PageRange` up to the UI. The
  translation to PyMuPDF's 0-based API happens only inside `PdfEngineAdapter`.

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

---

## 🚀 Running the Application

```bash
python main.py
```

> La UI de Qt todavía no está conectada. `main.py` levanta una CLI provisional
> que pide la ruta del PDF y la selección de páginas (`1-5,10-15`), y ejecuta
> el mismo `SplitPdfUseCase` que consumirá la ventana.

---

## 🧪 Tests

```bash
pytest kobun/tests            # todo
pytest kobun/tests/unit       # dominio puro, sin dependencias
```

Los tests de `integration/` generan PDFs reales con PyMuPDF y verifican que se
extraigan exactamente las páginas pedidas. Se omiten solos si PyMuPDF no está
instalado.

---

## 📂 Example Workflow

1. Select `book.pdf`
2. Enter a page selection: `25-40`, or `1-5,10-15,20` for several sections at once
3. Click **Export**
4. Receive a PDF with exactly those pages, in that order

Desde código:

```python
selection = PageSelection.parse("1-5,10-15")
use_case.execute(Path("book.pdf"), Path("out.pdf"), selection)
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
- [ ] Qt UI wired to the use cases
- [ ] Light / dark theme system
- [ ] Batch splitting
- [ ] CLI version
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

---

## 📄 License

Released under the MIT License.  
See `LICENSE` for details.
