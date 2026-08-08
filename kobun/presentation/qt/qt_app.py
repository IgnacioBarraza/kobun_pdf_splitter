import sys
from typing import List, Optional

from PySide6.QtWidgets import QApplication

from kobun.application.services.output_path_resolver import OutputPathResolver
from kobun.application.services.theme_service import ThemeService
from kobun.application.use_cases.list_history_use_case import ListHistoryUseCase
from kobun.application.use_cases.load_pdf_use_case import LoadPdfUseCase
from kobun.application.use_cases.record_split_use_case import RecordSplitUseCase
from kobun.application.use_cases.split_pdf_use_case import SplitPdfUseCase
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService
from kobun.infrastructure.config.infrastructure_settings import AppDirectories
from kobun.infrastructure.filesystem.local_file_storage import LocalFileStorage
from kobun.infrastructure.pdf_engine.pdf_engine_adapter import PdfEngineAdapter
from kobun.infrastructure.repositories.json_history_repository import JsonHistoryRepository
from kobun.infrastructure.repositories.json_preferences_repository import (
    JsonPreferencesRepository,
)
from kobun.infrastructure.repositories.pdf_repository_impl import PyMuPdfRepository
from kobun.infrastructure.ui.theme_loader import JsonThemeSource
from kobun.presentation.qt.app_icon import load_app_icon
from kobun.presentation.qt.windows.main_window import MainWindow
from kobun.presentation.viewmodels.pdf_view_model import PdfViewModel
from kobun.shared.config.app_settings import (
    APP_ID,
    APP_NAME,
    HISTORY_FILENAME,
    PREFERENCES_FILENAME,
)


class KobunApplication:
    """
    Punto de ensamblado: es el único lugar donde se eligen implementaciones
    concretas. Todo lo demás recibe sus dependencias ya construidas.
    """

    def __init__(self, directories: Optional[AppDirectories] = None):
        self._directories = directories or AppDirectories()

        file_storage = LocalFileStorage()
        pdf_repository = PyMuPdfRepository(PdfEngineAdapter())
        pdf_service = PdfSplitterService()

        self._history_repository = JsonHistoryRepository(
            self._directories.data_file(HISTORY_FILENAME)
        )
        preferences_repository = JsonPreferencesRepository(
            self._directories.config_file(PREFERENCES_FILENAME)
        )

        self._theme_service = ThemeService(preferences_repository, JsonThemeSource())

        self._view_model = PdfViewModel(
            load_use_case=LoadPdfUseCase(pdf_repository, pdf_service),
            split_use_case=SplitPdfUseCase(
                pdf_repository, pdf_service, OutputPathResolver(file_storage)
            ),
            record_use_case=RecordSplitUseCase(self._history_repository),
            list_history_use_case=ListHistoryUseCase(self._history_repository, file_storage),
            file_storage=file_storage,
        )

    def build_window(self) -> MainWindow:
        return MainWindow(self._view_model, self._theme_service, self._history_repository)


def run(argv: Optional[List[str]] = None) -> int:
    """
    Levanta la ventana y entra al bucle de eventos de Qt.
    """
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName(APP_NAME)

    # Fusion es el estilo propio de Qt y no el del sistema. Sin esto, parte
    # del QSS queda pisada por el tema nativo y la ventana se ve distinta en
    # cada máquina: era lo que hacía asomar el estilo de Ubuntu.
    app.setStyle("Fusion")

    # Declara el app_id del escritorio. En Wayland es lo único que permite al
    # compositor asociar la ventana con su .desktop —y por lo tanto con su
    # icono—; sin esto el app_id sería "python3".
    app.setDesktopFileName(APP_ID)

    # Sigue haciendo falta para X11 y Windows, donde el icono viaja con la
    # ventana en lugar de resolverse por app_id.
    app.setWindowIcon(load_app_icon())

    window = KobunApplication().build_window()
    window.show()

    return app.exec()
