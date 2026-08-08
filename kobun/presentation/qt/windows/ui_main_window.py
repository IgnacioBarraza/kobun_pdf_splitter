from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from kobun.presentation.qt.windows.drag_drop_area import DragDropArea
from kobun.presentation.qt.windows.split_options_widget import SplitOptionsWidget

SPLIT_PAGE = 0
HISTORY_PAGE = 1


class Ui_MainWindow:
    """
    Construcción de la interfaz, sin ninguna lógica.

    Los widgets no llevan estilos propios: todo el color sale del QSS que
    genera StyleGenerator, para que alternar tema sea reemplazar una hoja.
    """

    def setupUi(self, MainWindow) -> None:
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowTitle("Kobun")
        MainWindow.resize(1000, 680)

        self.central_widget = QWidget(MainWindow)
        root = QHBoxLayout(self.central_widget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content(), stretch=1)

        MainWindow.setCentralWidget(self.central_widget)

    # =========================
    # Sidebar
    # =========================

    def _build_sidebar(self) -> QFrame:
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(210)

        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(8)

        self.label_logo = QLabel("KOBUN")
        self.label_logo.setObjectName("Logo")
        layout.addWidget(self.label_logo)

        self.label_tagline = QLabel("Dividir PDFs")
        self.label_tagline.setObjectName("SecondaryText")
        layout.addWidget(self.label_tagline)
        layout.addSpacing(20)

        self.btn_split = self._nav_button("Dividir PDF", checked=True)
        layout.addWidget(self.btn_split)

        self.btn_history = self._nav_button("Historial")
        layout.addWidget(self.btn_history)

        layout.addStretch()

        self.label_theme = QLabel("Tema")
        self.label_theme.setObjectName("SecondaryText")
        layout.addWidget(self.label_theme)

        self.combo_theme = QComboBox()
        layout.addWidget(self.combo_theme)

        return self.sidebar

    @staticmethod
    def _nav_button(text: str, checked: bool = False) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("NavButton")
        button.setCheckable(True)
        button.setChecked(checked)
        button.setAutoExclusive(True)

        return button

    # =========================
    # Contenido
    # =========================

    def _build_content(self) -> QFrame:
        self.content_area = QFrame()
        self.content_area.setObjectName("MainContainer")

        layout = QVBoxLayout(self.content_area)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_split_page())
        self.pages.addWidget(self._build_history_page())
        layout.addWidget(self.pages, stretch=1)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminado: no sabemos cuánto falta.
        self.progress.setTextVisible(False)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.label_status = QLabel("")
        self.label_status.setWordWrap(True)
        layout.addWidget(self.label_status)

        return self.content_area

    def _build_split_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.title_split = QLabel("Dividir documento")
        self.title_split.setObjectName("Title")
        layout.addWidget(self.title_split)

        self.drop_area = DragDropArea()
        layout.addWidget(self.drop_area)

        self.split_options = SplitOptionsWidget()
        layout.addWidget(self.split_options)

        layout.addStretch()

        self.btn_process = QPushButton("DIVIDIR PDF")
        self.btn_process.setObjectName("PrimaryButton")
        self.btn_process.setMinimumHeight(44)
        self.btn_process.setEnabled(False)
        layout.addWidget(self.btn_process)

        return page

    def _build_history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.title_history = QLabel("Historial de exportaciones")
        self.title_history.setObjectName("Title")
        layout.addWidget(self.title_history)

        self.label_history_hint = QLabel(
            "Doble clic para abrir. Las entradas marcadas con ✗ ya no están en disco."
        )
        self.label_history_hint.setObjectName("SecondaryText")
        layout.addWidget(self.label_history_hint)

        self.list_history = QListWidget()
        self.list_history.setAlternatingRowColors(False)
        layout.addWidget(self.list_history, stretch=1)

        actions = QHBoxLayout()
        actions.addStretch()

        self.btn_open_export = QPushButton("Abrir seleccionado")
        self.btn_open_export.setEnabled(False)
        actions.addWidget(self.btn_open_export)

        self.btn_clear_history = QPushButton("Limpiar historial")
        actions.addWidget(self.btn_clear_history)

        layout.addLayout(actions)

        return page
