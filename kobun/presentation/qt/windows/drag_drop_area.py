from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QFrame, QLabel, QPushButton, QVBoxLayout

PLACEHOLDER = "Arrastrá un PDF acá"
HINT = "o hacé clic en Seleccionar archivo"


class DragDropArea(QFrame):
    """
    An area to drop a PDF on, or to open the file dialog from.

    It does not validate the file's contents: it only filters by extension to
    give immediate visual feedback. The real validation —that it is a readable
    PDF, not encrypted, with pages— is LoadPdfUseCase's job, the only place
    that rule should live.
    """

    file_dropped = Signal(Path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropArea")
        self.setAcceptDrops(True)
        self.setMinimumHeight(172)
        self.setProperty("dragActive", False)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        self.label_file = QLabel(PLACEHOLDER)
        self.label_file.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_file)

        self.label_details = QLabel(HINT)
        self.label_details.setObjectName("SecondaryText")
        self.label_details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_details)

        self.btn_browse = QPushButton("Seleccionar archivo")
        self.btn_browse.clicked.connect(self._browse)
        layout.addWidget(self.btn_browse, alignment=Qt.AlignmentFlag.AlignCenter)

    # =========================
    # Presentation
    # =========================

    def show_document(self, filename: str, details: str) -> None:
        self.label_file.setText(filename)
        self.label_details.setText(details)

    def show_placeholder(self) -> None:
        self.label_file.setText(PLACEHOLDER)
        self.label_details.setText(HINT)

    # =========================
    # Drag & drop
    # =========================

    def dragEnterEvent(self, event) -> None:
        if self._first_pdf(event) is None:
            event.ignore()
            return

        self._set_drag_active(True)
        event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self._set_drag_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:
        self._set_drag_active(False)
        path = self._first_pdf(event)

        if path is None:
            event.ignore()
            return

        event.acceptProposedAction()
        self.file_dropped.emit(path)

    @staticmethod
    def _first_pdf(event) -> Optional[Path]:
        """
        When several files are dropped the first PDF is taken and the rest
        ignored: the screen works on one document at a time.
        """
        mime = event.mimeData()
        if not mime.hasUrls():
            return None

        candidates: List[Path] = [
            Path(url.toLocalFile())
            for url in mime.urls()
            if url.isLocalFile()
        ]

        for candidate in candidates:
            if candidate.suffix.lower() == ".pdf":
                return candidate

        return None

    def _set_drag_active(self, active: bool) -> None:
        self.setProperty("dragActive", active)
        # Qt does not re-evaluate property selectors until asked to.
        self.style().unpolish(self)
        self.style().polish(self)

    def _browse(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar PDF", "", "Documentos PDF (*.pdf)"
        )

        if filename:
            self.file_dropped.emit(Path(filename))
