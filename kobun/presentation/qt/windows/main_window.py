from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem, QMainWindow

from kobun.application.interfaces.history_repository import HistoryRepository
from kobun.application.services.theme_service import ThemeService
from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.presentation import error_messages
from kobun.presentation.qt import dialogs
from kobun.presentation.qt.styles.style_generator import StyleGenerator
from kobun.presentation.qt.windows.ui_main_window import HISTORY_PAGE, SPLIT_PAGE, Ui_MainWindow
from kobun.presentation.viewmodels.pdf_view_model import PdfViewModel

RECORD_ROLE = Qt.ItemDataRole.UserRole

CLEAR_HISTORY_QUESTION = (
    "Se va a borrar todo el historial de exportaciones.\n\n"
    "Los PDFs generados no se tocan; sólo se pierde el registro."
)


class MainWindow(QMainWindow):
    """
    Ventana principal: traduce interacciones a llamadas del viewmodel y
    señales del viewmodel a cambios visibles.

    No conoce use cases ni excepciones del dominio salvo para pedirle un
    mensaje a `error_messages`.
    """

    def __init__(
        self,
        view_model: PdfViewModel,
        theme_service: ThemeService,
        history_repository: HistoryRepository,
        show_error: Optional[Callable] = None,
        ask_confirmation: Optional[Callable] = None,
    ):
        super().__init__()
        self._view_model = view_model
        self._theme_service = theme_service
        self._history_repository = history_repository

        # Inyectables para poder verificar qué diálogo se abre sin que un
        # modal bloquee la suite de tests esperando un clic.
        self._show_error = show_error or dialogs.show_error
        self._ask_confirmation = ask_confirmation or dialogs.ask_confirmation

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self._populate_themes()
        self.apply_theme(self._theme_service.current())
        self._connect()
        self._view_model.refresh_history()

    # =========================
    # Tema
    # =========================

    def apply_theme(self, theme) -> None:
        self.setStyleSheet(StyleGenerator.generate(theme))

    def select_theme(self, theme_name: str) -> None:
        self.apply_theme(self._theme_service.select(theme_name))

    def _populate_themes(self) -> None:
        """
        Carga el catálogo y preselecciona el tema activo.

        Las señales se bloquean mientras se arma la lista: `setCurrentIndex`
        emitiría `currentIndexChanged` y volvería a guardar la preferencia
        durante el arranque, por un cambio que el usuario no hizo.
        """
        combo = self.ui.combo_theme
        activo = self._theme_service.current().name

        combo.blockSignals(True)
        try:
            grupo_oscuro = False

            for theme in self._theme_service.available():
                # Con muchas paletas conviene separar claros de oscuros: la
                # agrupación sale de la luminancia del fondo, así que un tema
                # nuevo cae solo en su grupo.
                if theme.is_dark and not grupo_oscuro:
                    if combo.count():
                        combo.insertSeparator(combo.count())
                    grupo_oscuro = True

                combo.addItem(theme.display_name, theme.name)

            indice = combo.findData(activo)
            if indice >= 0:
                combo.setCurrentIndex(indice)
        finally:
            combo.blockSignals(False)

    def _on_theme_chosen(self, index: int) -> None:
        name = self.ui.combo_theme.itemData(index)

        if name:
            self.select_theme(str(name))

    # =========================
    # Cableado
    # =========================

    def _connect(self) -> None:
        ui = self.ui

        ui.btn_split.clicked.connect(lambda: ui.pages.setCurrentIndex(SPLIT_PAGE))
        ui.btn_history.clicked.connect(self._show_history)
        ui.combo_theme.currentIndexChanged.connect(self._on_theme_chosen)

        ui.drop_area.file_dropped.connect(self._on_file_chosen)
        ui.split_options.selection_changed.connect(self._on_selection_changed)
        ui.btn_process.clicked.connect(self._on_split_requested)

        ui.list_history.itemSelectionChanged.connect(self._on_history_selection_changed)
        ui.list_history.itemDoubleClicked.connect(self._open_history_item)
        ui.btn_open_export.clicked.connect(self._open_selected_export)
        ui.btn_clear_history.clicked.connect(self._clear_history)

        self._view_model.document_loaded.connect(self._on_document_loaded)
        self._view_model.split_succeeded.connect(self._on_split_succeeded)
        self._view_model.history_changed.connect(self._render_history)
        self._view_model.busy_changed.connect(self._on_busy_changed)

        # Lo que el usuario pidió y falló lo interrumpe con un diálogo.
        self._view_model.load_failed.connect(self._report_blocking_error)
        self._view_model.split_failed.connect(self._report_blocking_error)

        # El historial es secundario: si no se puede escribir o leer, el PDF
        # ya se generó y un modal sería alarmista.
        self._view_model.history_failed.connect(self._report_minor_error)

    # =========================
    # Carga
    # =========================

    def _on_file_chosen(self, path: Path) -> None:
        self._set_status(f"Abriendo {path.name}...")
        self._view_model.load_document(path)

    def _on_document_loaded(self, document) -> None:
        self.ui.drop_area.show_document(
            document.filename,
            f"{document.page_count} páginas · {document.metadata.title}",
        )
        self.ui.split_options.set_directory(document.storage_path.parent)
        self._set_status(f"{document.filename} listo para dividir.")
        self._refresh_actions()

    # =========================
    # División
    # =========================

    def _on_selection_changed(self, _text: str) -> None:
        self._refresh_actions()

        selection = self._parse_selection()
        if selection is not None:
            self.ui.split_options.set_suggested_destination(
                self._view_model.suggested_output_path(selection)
            )

    def _on_split_requested(self) -> None:
        selection = self._parse_selection()
        if selection is None:
            self._set_status("Revisá el rango de páginas.", error=True)
            return

        self._set_status("Procesando...")
        self._view_model.split(
            selection=selection,
            output_path=self.ui.split_options.destination,
            policy=self.ui.split_options.policy,
        )

    def _on_split_succeeded(self, response) -> None:
        self._set_status(
            f"Listo: {response.output_filename} ({response.page_count} páginas)",
            success=True,
        )
        self.ui.split_options.clear()

    def _parse_selection(self) -> Optional[PageSelection]:
        raw = self.ui.split_options.selection_text
        if not raw:
            return None

        try:
            return PageSelection.parse(raw)
        except InvalidPageRangeException:
            return None

    # =========================
    # Historial
    # =========================

    def _show_history(self) -> None:
        self._view_model.refresh_history()
        self.ui.pages.setCurrentIndex(HISTORY_PAGE)

    def _render_history(self, entries) -> None:
        self.ui.list_history.clear()

        for entry in entries:
            item = QListWidgetItem(self._history_label(entry))
            item.setData(RECORD_ROLE, entry)
            item.setToolTip(self._history_detail(entry))

            self.ui.list_history.addItem(item)

        self._on_history_selection_changed()

    @staticmethod
    def _history_label(entry) -> str:
        """
        La lista muestra sólo el archivo generado: es lo que el usuario busca
        cuando abre el historial. El origen y los rangos quedan en el tooltip.
        """
        cuando = entry.record.created_at.astimezone().strftime("%d/%m/%Y %H:%M")
        marca = "" if entry.is_available else "✗ "

        return f"{marca}{cuando}   {entry.record.output_filename}"

    @staticmethod
    def _history_detail(entry) -> str:
        record = entry.record
        lineas = [
            f"Origen: {record.source_filename}",
            f"Páginas: {record.selection}  ({record.page_count} en total)",
            f"Ubicación: {record.output_path}",
        ]

        if not entry.is_available:
            lineas.append("El archivo ya no está en esta ubicación.")

        return "\n".join(lineas)

    def _on_history_selection_changed(self) -> None:
        entry = self._selected_entry()
        self.ui.btn_open_export.setEnabled(entry is not None and entry.is_available)

    def _selected_entry(self):
        item = self.ui.list_history.currentItem()

        return item.data(RECORD_ROLE) if item is not None else None

    def _open_history_item(self, item: QListWidgetItem) -> None:
        self._open_entry(item.data(RECORD_ROLE))

    def _open_selected_export(self) -> None:
        self._open_entry(self._selected_entry())

    def _open_entry(self, entry) -> None:
        if entry is None:
            return

        try:
            self._view_model.open_export(entry.record.output_path)
        except Exception as error:
            self._report_blocking_error(error)

    def _clear_history(self) -> None:
        if self.ui.list_history.count() == 0:
            return

        if not self._ask_confirmation(self, CLEAR_HISTORY_QUESTION, "Borrar historial"):
            return

        self._history_repository.clear()
        self._view_model.refresh_history()
        self._set_status("Historial vacío.")

    # =========================
    # Estado visual
    # =========================

    def _on_busy_changed(self, busy: bool) -> None:
        self.ui.progress.setVisible(busy)
        self.ui.split_options.set_enabled(not busy)
        self._refresh_actions()

    def _refresh_actions(self) -> None:
        listo = (
            self._view_model.has_document
            and not self._view_model.is_busy
            and self._parse_selection() is not None
        )
        self.ui.btn_process.setEnabled(listo)

    def _report_blocking_error(self, error: Exception) -> None:
        """
        Falló algo que el usuario pidió explícitamente: diálogo modal, y el
        mensaje queda además en la barra de estado como recordatorio de qué
        pasó una vez cerrado.
        """
        self._report_minor_error(error)
        self._show_error(self, error)

    def _report_minor_error(self, error: Exception) -> None:
        self._set_status(error_messages.translate(error), error=True)

        if not error_messages.is_expected(error):
            # Un bug nuestro: el usuario ve un mensaje genérico y el detalle
            # queda visible en consola para poder reportarlo.
            print(f"[ERROR INESPERADO] {error_messages.technical_detail(error)}")

    def _set_status(self, message: str, error: bool = False, success: bool = False) -> None:
        label = self.ui.label_status
        label.setText(message)
        label.setObjectName("ErrorText" if error else "SuccessText" if success else "")

        # Cambiar objectName exige recalcular el estilo del widget.
        label.style().unpolish(label)
        label.style().polish(label)
