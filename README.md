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

- Desktop interface built with **PySide6 (Qt for Python)**
- PDF processing powered by **PyMuPDF**
- Select any local PDF file
- Extract specific page ranges (e.g., `1-10`, `25-40`)
- Generate a new PDF containing only selected pages
- Open the exported PDF directly from the application
- Recently exported files history
- Strict domain validation for invalid page ranges
- Explicit domain-level exceptions

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
```

### Architectural Principles

- Immutable Value Objects
- Explicit domain exceptions
- No framework leakage into the domain layer
- Deterministic validation of page ranges
- Clear dependency direction (outer layers depend on inner layers)

---

## 🛠 Requirements

- Python **3.10+**
- pip

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Application

```bash
python main.py
```

> Adjust the entry point if your structure differs.

---

## 📂 Example Workflow

1. Select `book.pdf`
2. Enter page range `25-40`
3. Click **Export**
4. Receive `book_25-40.pdf`

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
- [ ] Batch splitting
- [ ] CLI version
- [ ] Cross-platform packaging (Windows / macOS / Linux)
- [ ] Automated tests for domain layer
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
