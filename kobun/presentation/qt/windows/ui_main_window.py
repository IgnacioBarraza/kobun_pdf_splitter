from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QFrame, QPushButton, QLineEdit, QLabel, QStackedWidget)
from PySide6.QtCore import Qt


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 700)

        self.central_widget = QWidget(MainWindow)
        self.layout = QHBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # --- SIDEBAR ---
        self.sidebar = QFrame(self.central_widget)
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setMinimumWidth(200)
        self.sidebar_layout = QVBoxLayout(self.sidebar)

        self.label_logo = QLabel("KOBUN")
        self.label_logo.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        self.sidebar_layout.addWidget(self.label_logo)

        self.btn_split = QPushButton("Split PDF")
        self.sidebar_layout.addWidget(self.btn_split)

        self.btn_history = QPushButton("Historial")
        self.sidebar_layout.addWidget(self.btn_history)

        self.sidebar_layout.addStretch()

        # Botón para cambiar tema (Prueba del sistema de temas)
        self.btn_toggle_theme = QPushButton("Cambiar Tema")
        self.sidebar_layout.addWidget(self.btn_toggle_theme)

        # --- MAIN CONTENT AREA ---
        self.content_area = QFrame(self.central_widget)
        self.content_area.setObjectName("MainContainer")
        self.content_layout = QVBoxLayout(self.content_area)

        self.title = QLabel("Split PDF Document")
        self.title.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.content_layout.addWidget(self.title)

        # Formulario Simple
        self.content_layout.addWidget(QLabel("Source PDF File"))
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText("Selecciona un archivo...")
        self.content_layout.addWidget(self.input_path)

        self.btn_process = QPushButton("SPLIT PDF")
        self.btn_process.setObjectName("PrimaryButton")
        self.btn_process.setMinimumHeight(45)
        self.content_layout.addWidget(self.btn_process)

        self.content_layout.addStretch()

        # Unir todo
        self.layout.addWidget(self.sidebar)
        self.layout.addWidget(self.content_area)
        MainWindow.setCentralWidget(self.central_widget)