from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from kobun.domain.pdf.value_objects.overwrite_policy import OverwritePolicy
from kobun.domain.pdf.services.pdf_splitter_service import PDF_SUFFIX

POLICY_LABELS = {
    OverwritePolicy.FAIL: "Avisar si el archivo ya existe",
    OverwritePolicy.RENAME: "Guardar con un nombre libre",
    OverwritePolicy.OVERWRITE: "Reemplazar el archivo existente",
}

NO_FOLDER = "Elegí un PDF para definir la carpeta de destino."


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

        # El campo muestra sólo el nombre del archivo; la carpeta se guarda
        # aparte y se informa debajo. Mostrar la ruta completa en el campo la
        # volvía ilegible y no era lo que el usuario necesita editar.
        self._directory: Optional[Path] = None

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
        layout.addWidget(QLabel("Nombre del archivo"))

        destination_row = QHBoxLayout()
        destination_row.setSpacing(6)

        self.input_output = QLineEdit()
        self.input_output.setPlaceholderText("Se sugiere al elegir las páginas")
        destination_row.addWidget(self.input_output)

        self.btn_browse_output = QPushButton("Examinar")
        self.btn_browse_output.clicked.connect(self._browse_output)
        destination_row.addWidget(self.btn_browse_output)

        layout.addLayout(destination_row)

        self.label_folder = QLabel(NO_FOLDER)
        self.label_folder.setObjectName("SecondaryText")
        # Ignored en horizontal: sin esto el sizeHint de una ruta larga expande
        # el layout más allá de la ventana y el texto se corta contra el borde
        # en lugar de recortarse con puntos suspensivos.
        self.label_folder.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.label_folder)

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
    def output_name(self) -> str:
        return self.input_output.text().strip()

    @property
    def destination(self) -> Optional[Path]:
        """
        Ruta completa a escribir: la carpeta recordada más el nombre tipeado.

        Devuelve None si no hay nombre, para que el use case caiga en su ruta
        sugerida. Agrega la extensión si falta: el campo pide un nombre, así
        que exigirle al usuario que escriba ".pdf" sería un error evitable.
        """
        name = self.output_name
        if not name or self._directory is None:
            return None

        if Path(name).suffix.lower() != PDF_SUFFIX:
            name = f"{name}{PDF_SUFFIX}"

        return self._directory / name

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

    def set_directory(self, directory: Optional[Path]) -> None:
        """
        Carpeta donde se escribirá. Se fija al cargar un documento y puede
        cambiarla el diálogo de guardado.
        """
        self._directory = Path(directory) if directory is not None else None
        self._render_folder()

    def set_destination(self, path: Path) -> None:
        """
        Fija carpeta y nombre a partir de una ruta completa.
        """
        path = Path(path)
        self.set_directory(path.parent)
        self.input_output.setText(path.name)

    def set_suggested_destination(self, path: Optional[Path]) -> None:
        """
        Precarga el destino sugerido. Nunca pisa lo que el usuario escribió.
        """
        if path is not None and not self.output_name:
            self.set_destination(path)

    def clear(self) -> None:
        self.input_selection.clear()
        self.input_output.clear()

    def set_enabled(self, enabled: bool) -> None:
        self.input_selection.setEnabled(enabled)
        self.input_output.setEnabled(enabled)
        self.btn_browse_output.setEnabled(enabled)
        self.combo_policy.setEnabled(enabled)

    def resizeEvent(self, event) -> None:
        # La ruta de la carpeta puede ser larguísima; se recorta al ancho
        # disponible para que no ensanche la ventana.
        super().resizeEvent(event)
        self._render_folder()

    def showEvent(self, event) -> None:
        # Al fijar la carpeta el layout todavía no corrió, así que el ancho
        # disponible era el inicial. Se recalcula cuando ya hay geometría real.
        super().showEvent(event)
        self._render_folder()

    def _render_folder(self) -> None:
        if self._directory is None:
            self.label_folder.setText(NO_FOLDER)
            self.label_folder.setToolTip("")
            return

        completa = str(self._directory)
        metrics = QFontMetrics(self.label_folder.font())
        # Se mide contra el ancho del widget contenedor: el del label es
        # "Ignored", así que no refleja un límite útil.
        disponible = max(self.width() - 90, 120)

        self.label_folder.setText(
            f"Carpeta: {metrics.elidedText(completa, Qt.TextElideMode.ElideMiddle, disponible)}"
        )
        self.label_folder.setToolTip(completa)

    def _browse_output(self) -> None:
        actual = self.destination or self._directory or Path.home()
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF como", str(actual), "Documentos PDF (*.pdf)"
        )

        if filename:
            self.set_destination(Path(filename))
