from pathlib import Path
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kobun.domain.pdf.value_objects.overwrite_policy import OverwritePolicy

POLICY_LABELS = {
    OverwritePolicy.FAIL: "Avisar si el archivo ya existe",
    OverwritePolicy.RENAME: "Guardar con un nombre libre",
    OverwritePolicy.OVERWRITE: "Reemplazar el archivo existente",
}


class SplitOptionsWidget(QWidget):
    """
    Rangos de páginas, destino y política de sobrescritura.

    Sólo recolecta lo que el usuario escribe; no valida ni parsea. El texto va
    tal cual a PageSelection.parse y la ruta a la política de salida, que son
    quienes saben qué es válido.
    """

    selection_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        layout.addWidget(QLabel("Páginas a extraer"))
        self.input_selection = QLineEdit()
        self.input_selection.setPlaceholderText("1-5,10-15  ·  7  ·  20-40")
        self.input_selection.textChanged.connect(self.selection_changed)
        layout.addWidget(self.input_selection)

        self.label_hint = QLabel("Separá los rangos con comas.")
        self.label_hint.setObjectName("SecondaryText")
        layout.addWidget(self.label_hint)

        layout.addSpacing(8)
        layout.addWidget(QLabel("Guardar en"))

        destination_row = QHBoxLayout()
        destination_row.setSpacing(6)

        self.input_output = QLineEdit()
        self.input_output.setPlaceholderText("Se sugiere al elegir las páginas")
        destination_row.addWidget(self.input_output)

        self.btn_browse_output = QPushButton("Examinar")
        self.btn_browse_output.clicked.connect(self._browse_output)
        destination_row.addWidget(self.btn_browse_output)

        layout.addLayout(destination_row)

        layout.addSpacing(8)
        layout.addWidget(QLabel("Si el destino ya existe"))
        self.combo_policy = QComboBox()
        for policy, label in POLICY_LABELS.items():
            self.combo_policy.addItem(label, policy)
        layout.addWidget(self.combo_policy)

    # =========================
    # Lectura
    # =========================

    @property
    def selection_text(self) -> str:
        return self.input_selection.text().strip()

    @property
    def output_path(self) -> Optional[Path]:
        raw = self.input_output.text().strip()

        return Path(raw) if raw else None

    @property
    def policy(self) -> OverwritePolicy:
        """
        Qt guarda la data de los items como QVariant y devuelve el enum
        convertido a str plano, así que hay que reconstruirlo. Sin esto el
        resto del sistema recibe "rename" en lugar de OverwritePolicy.RENAME.
        """
        return OverwritePolicy(self.combo_policy.currentData())

    def set_policy(self, policy: OverwritePolicy) -> None:
        for index in range(self.combo_policy.count()):
            if self.combo_policy.itemData(index) == policy:
                self.combo_policy.setCurrentIndex(index)
                return

    # =========================
    # Escritura
    # =========================

    def set_suggested_output(self, path: Optional[Path]) -> None:
        """
        Precarga el destino sugerido. Nunca pisa lo que el usuario escribió.
        """
        if path is not None and not self.input_output.text().strip():
            self.input_output.setText(str(path))

    def clear(self) -> None:
        self.input_selection.clear()
        self.input_output.clear()

    def set_enabled(self, enabled: bool) -> None:
        self.input_selection.setEnabled(enabled)
        self.input_output.setEnabled(enabled)
        self.btn_browse_output.setEnabled(enabled)
        self.combo_policy.setEnabled(enabled)

    def _browse_output(self) -> None:
        current = self.input_output.text().strip()
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF como", current, "Documentos PDF (*.pdf)"
        )

        if filename:
            self.input_output.setText(filename)
