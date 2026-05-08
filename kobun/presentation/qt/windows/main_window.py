from pathlib import Path
from PySide6.QtWidgets import QMainWindow
from kobun.presentation.qt.ui_main_window import Ui_MainWindow
from kobun.infrastructure.ui.theme_loader import ThemeLoader
from kobun.presentation.qt.styles.style_generator import StyleGenerator


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Estado del tema para el toggle
        self.current_theme_is_dark = False

        # Rutas a tus JSON (Asegúrate de que existan en esa carpeta)
        self.themes_path = Path("themes")  # O la carpeta donde los tengas

        # Cargar tema inicial
        self.apply_app_theme("light.json")

        # Conectar señales
        self.ui.btn_toggle_theme.clicked.connect(self.toggle_theme)

    def apply_app_theme(self, theme_file: str):
        try:
            theme_path = self.themes_path / theme_file
            theme_vo = ThemeLoader.load_from_json(theme_path)
            qss = StyleGenerator.generate(theme_vo)
            self.setStyleSheet(qss)
        except Exception as e:
            print(f"Error cargando tema: {e}")

    def toggle_theme(self):
        if self.current_theme_is_dark:
            self.apply_app_theme("light.json")
            self.current_theme_is_dark = False
        else:
            self.apply_app_theme("dark.json")
            self.current_theme_is_dark = True