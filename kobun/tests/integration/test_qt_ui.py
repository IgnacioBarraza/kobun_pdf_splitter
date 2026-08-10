"""
Tests de la interfaz sobre PDFs reales, corriendo Qt en modo offscreen.

Verifican el ciclo completo que atraviesa todas las capas: soltar un archivo,
cargarlo en el pool de hilos, dividirlo, registrar el historial y repintar la
ventana. Se omiten si falta PySide6 o PyMuPDF.
"""
import os

import pytest

pymupdf = pytest.importorskip("pymupdf", reason="PyMuPDF no instalado")
pytest.importorskip("PySide6", reason="PySide6 no instalado")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QThreadPool  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from kobun.application.services.output_path_resolver import OutputPathResolver  # noqa: E402
from kobun.application.services.theme_service import ThemeService  # noqa: E402
from kobun.application.use_cases.list_history_use_case import ListHistoryUseCase  # noqa: E402
from kobun.application.use_cases.load_pdf_use_case import LoadPdfUseCase  # noqa: E402
from kobun.application.use_cases.record_split_use_case import RecordSplitUseCase  # noqa: E402
from kobun.application.use_cases.split_pdf_use_case import SplitPdfUseCase  # noqa: E402
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService  # noqa: E402
from kobun.domain.pdf.value_objects.overwrite_policy import OverwritePolicy  # noqa: E402
from kobun.infrastructure.filesystem.local_file_storage import LocalFileStorage  # noqa: E402
from kobun.infrastructure.pdf_engine.pdf_engine_adapter import PdfEngineAdapter  # noqa: E402
from kobun.infrastructure.repositories.json_history_repository import (  # noqa: E402
    JsonHistoryRepository,
)
from kobun.infrastructure.repositories.json_preferences_repository import (  # noqa: E402
    JsonPreferencesRepository,
)
from kobun.infrastructure.repositories.pdf_repository_impl import PyMuPdfRepository  # noqa: E402
from kobun.infrastructure.ui.theme_loader import JsonThemeSource  # noqa: E402
from kobun.presentation.qt.windows.main_window import MainWindow  # noqa: E402
from kobun.presentation.viewmodels.pdf_view_model import PdfViewModel  # noqa: E402
from kobun.shared.config.theme_settings import (  # noqa: E402
    AVAILABLE_THEMES,
    DARK_THEME,
    LIGHT_THEME,
)

TIMEOUT_MS = 15000


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def source_pdf(tmp_path):
    path = tmp_path / "libro.pdf"

    doc = pymupdf.open()
    for number in range(1, 13):
        page = doc.new_page()
        page.insert_text((72, 144), f"PAGINA {number}", fontsize=40)
    doc.set_metadata({"title": "Libro Original", "author": "Ignacio"})
    doc.save(path)
    doc.close()

    return path


class DialogRecorder:
    """
    Sustituye a los diálogos modales: sin esto, un QMessageBox esperando un
    clic dejaría la suite colgada esperando que alguien lo cierre.
    """

    def __init__(self, answer: bool = True):
        self.errors = []
        self.questions = []
        self.answer = answer

    def show_error(self, parent, error):
        self.errors.append(error)

    def ask_confirmation(self, parent, question, accept_text="Continuar"):
        self.questions.append(question)
        return self.answer


@pytest.fixture
def dialogs():
    return DialogRecorder()


@pytest.fixture
def window(qt_app, tmp_path, dialogs):
    file_storage = LocalFileStorage()
    pdf_repository = PyMuPdfRepository(PdfEngineAdapter())
    pdf_service = PdfSplitterService()

    history_repository = JsonHistoryRepository(tmp_path / "datos" / "history.json")
    preferences = JsonPreferencesRepository(tmp_path / "config" / "preferences.json")

    view_model = PdfViewModel(
        load_use_case=LoadPdfUseCase(pdf_repository, pdf_service),
        split_use_case=SplitPdfUseCase(
            pdf_repository, pdf_service, OutputPathResolver(file_storage)
        ),
        record_use_case=RecordSplitUseCase(history_repository),
        list_history_use_case=ListHistoryUseCase(history_repository, file_storage),
        file_storage=file_storage,
    )

    ventana = MainWindow(
        view_model,
        ThemeService(preferences, JsonThemeSource()),
        history_repository,
        show_error=dialogs.show_error,
        ask_confirmation=dialogs.ask_confirmation,
    )

    ventana.show()
    yield ventana

    ventana.close()


def settle(qt_app) -> None:
    """
    Espera a que el pool de hilos termine y procesa los eventos pendientes,
    que es cómo llegan los resultados desde el worker al hilo principal.

    Se procesa varias veces a propósito: `processEvents` no atiende lo que se
    encola *durante* su propia ejecución, y un slot puede emitir señales que
    disparan más trabajo. Con una sola pasada los tests aprueban en offscreen
    pero se vuelven sensibles al timing en un compositor real.
    """
    QThreadPool.globalInstance().waitForDone(TIMEOUT_MS)

    for _ in range(3):
        qt_app.processEvents()


def load(window, qt_app, path):
    window.ui.drop_area.file_dropped.emit(path)
    settle(qt_app)


# =========================
# Carga
# =========================

def test_dropping_a_pdf_loads_it_and_shows_its_details(window, qt_app, source_pdf):
    load(window, qt_app, source_pdf)

    assert window.ui.drop_area.label_file.text() == "libro.pdf"
    assert "12 páginas" in window.ui.drop_area.label_details.text()


def test_split_button_stays_disabled_until_file_and_range_are_ready(window, qt_app, source_pdf):
    assert window.ui.btn_process.isEnabled() is False

    load(window, qt_app, source_pdf)
    assert window.ui.btn_process.isEnabled() is False, "Falta el rango"

    window.ui.split_options.input_selection.setText("1-3")
    assert window.ui.btn_process.isEnabled() is True


def test_an_invalid_range_keeps_the_button_disabled(window, qt_app, source_pdf):
    load(window, qt_app, source_pdf)

    window.ui.split_options.input_selection.setText("10-2")

    assert window.ui.btn_process.isEnabled() is False


def test_a_corrupt_file_shows_a_friendly_message(window, qt_app, tmp_path):
    roto = tmp_path / "roto.pdf"
    roto.write_bytes(b"no soy un pdf")

    load(window, qt_app, roto)

    assert "no es un PDF" in window.ui.label_status.text()
    assert window.ui.btn_process.isEnabled() is False


def test_an_encrypted_file_shows_the_overridden_message(window, qt_app, tmp_path):
    protegido = tmp_path / "protegido.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(protegido, encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="d", user_pw="s")
    doc.close()

    load(window, qt_app, protegido)

    assert "contraseña" in window.ui.label_status.text()


# =========================
# División
# =========================

def test_the_suggested_output_appears_when_typing_a_range(window, qt_app, source_pdf):
    load(window, qt_app, source_pdf)

    window.ui.split_options.input_selection.setText("1-3,8")

    assert window.ui.split_options.input_output.text().endswith("libro_1-3_8.pdf")


def test_a_manual_destination_is_not_overwritten_by_the_suggestion(window, qt_app, source_pdf, tmp_path):
    load(window, qt_app, source_pdf)
    window.ui.split_options.set_destination(tmp_path / "mio.pdf")

    window.ui.split_options.input_selection.setText("1-3")

    assert window.ui.split_options.input_output.text() == "mio.pdf"


def test_the_destination_field_shows_only_the_filename(window, qt_app, source_pdf):
    load(window, qt_app, source_pdf)

    window.ui.split_options.input_selection.setText("1-3,8")

    assert window.ui.split_options.input_output.text() == "libro_1-3_8.pdf"
    assert "/" not in window.ui.split_options.input_output.text()


def test_the_folder_is_shown_separately(window, qt_app, source_pdf):
    load(window, qt_app, source_pdf)

    assert window.ui.split_options.label_folder.toolTip() == str(source_pdf.parent)
    assert "Carpeta:" in window.ui.split_options.label_folder.text()


def test_a_typed_name_lands_in_the_document_folder(window, qt_app, source_pdf):
    load(window, qt_app, source_pdf)
    window.ui.split_options.input_selection.setText("1-3")
    window.ui.split_options.input_output.setText("capitulo uno.pdf")

    assert window.ui.split_options.destination == source_pdf.parent / "capitulo uno.pdf"


def test_a_typed_name_without_extension_still_works(window, qt_app, source_pdf):
    """El campo pide un nombre, no una ruta: exigir ".pdf" sería un error evitable."""
    load(window, qt_app, source_pdf)
    window.ui.split_options.input_selection.setText("1-3")
    window.ui.split_options.input_output.setText("capitulo uno")

    window.ui.btn_process.click()
    settle(qt_app)

    assert (source_pdf.parent / "capitulo uno.pdf").exists()


def test_splitting_writes_the_file_and_reports_success(window, qt_app, source_pdf):
    load(window, qt_app, source_pdf)
    window.ui.split_options.input_selection.setText("1-3,8")

    window.ui.btn_process.click()
    settle(qt_app)

    generado = source_pdf.parent / "libro_1-3_8.pdf"
    assert generado.exists()
    assert "Listo" in window.ui.label_status.text()

    doc = pymupdf.open(generado)
    try:
        assert doc.page_count == 4
    finally:
        doc.close()


def test_the_ui_is_not_blocked_while_working(window, qt_app, source_pdf):
    """
    El trabajo va al pool: al disparar el split la ventana ya está marcada
    como ocupada, con el spinner visible y las opciones deshabilitadas,
    en lugar de haber quedado congelada hasta terminar.
    """
    load(window, qt_app, source_pdf)
    window.ui.split_options.input_selection.setText("1-3")

    window.ui.btn_process.click()
    ocupada_durante = window.ui.progress.isVisible()
    opciones_bloqueadas = not window.ui.split_options.input_selection.isEnabled()
    settle(qt_app)

    assert ocupada_durante is True
    assert opciones_bloqueadas is True
    assert window.ui.progress.isVisible() is False, "El spinner se oculta al terminar"
    assert window.ui.split_options.input_selection.isEnabled() is True


def test_an_existing_destination_is_reported_instead_of_overwritten(window, qt_app, source_pdf, tmp_path):
    ocupado = tmp_path / "ocupado.pdf"
    ocupado.write_bytes(b"contenido previo")

    load(window, qt_app, source_pdf)
    window.ui.split_options.input_selection.setText("1-3")
    window.ui.split_options.input_output.setText(str(ocupado))

    window.ui.btn_process.click()
    settle(qt_app)

    assert "ya existe" in window.ui.label_status.text()
    assert ocupado.read_bytes() == b"contenido previo"


def test_the_rename_policy_can_be_chosen_from_the_ui(window, qt_app, source_pdf, tmp_path):
    ocupado = tmp_path / "ocupado.pdf"
    ocupado.write_bytes(b"contenido previo")

    load(window, qt_app, source_pdf)
    window.ui.split_options.input_selection.setText("1-3")
    window.ui.split_options.set_destination(ocupado)
    window.ui.split_options.set_policy(OverwritePolicy.RENAME)

    window.ui.btn_process.click()
    settle(qt_app)

    assert (tmp_path / "ocupado_1.pdf").exists()
    assert ocupado.read_bytes() == b"contenido previo"


# =========================
# Historial
# =========================

def test_a_successful_split_appears_in_the_history(window, qt_app, source_pdf):
    load(window, qt_app, source_pdf)
    window.ui.split_options.input_selection.setText("2-4")
    window.ui.btn_process.click()
    settle(qt_app)

    assert window.ui.list_history.count() == 1
    assert window.ui.list_history.item(0).text().endswith("libro_2-4.pdf")


def test_the_history_row_shows_only_the_generated_file(window, qt_app, source_pdf):
    load(window, qt_app, source_pdf)
    window.ui.split_options.input_selection.setText("2-4")
    window.ui.btn_process.click()
    settle(qt_app)

    texto = window.ui.list_history.item(0).text()

    assert "libro_2-4.pdf" in texto
    assert "->" not in texto, "El origen y la flecha ensuciaban la fila"
    assert "[2-4]" not in texto


def test_the_history_tooltip_keeps_the_full_detail(window, qt_app, source_pdf):
    load(window, qt_app, source_pdf)
    window.ui.split_options.input_selection.setText("2-4")
    window.ui.btn_process.click()
    settle(qt_app)

    tooltip = window.ui.list_history.item(0).toolTip()

    assert "libro.pdf" in tooltip
    assert "2-4" in tooltip
    assert "3 en total" in tooltip


def test_deleted_exports_are_flagged_in_the_list(window, qt_app, source_pdf):
    load(window, qt_app, source_pdf)
    window.ui.split_options.input_selection.setText("2-4")
    window.ui.btn_process.click()
    settle(qt_app)

    (source_pdf.parent / "libro_2-4.pdf").unlink()
    window.ui.btn_history.click()
    settle(qt_app)

    item = window.ui.list_history.item(0)
    assert item.text().startswith("✗")
    assert window.ui.btn_open_export.isEnabled() is False


def test_clearing_the_history_empties_the_list(window, qt_app, source_pdf):
    load(window, qt_app, source_pdf)
    window.ui.split_options.input_selection.setText("2-4")
    window.ui.btn_process.click()
    settle(qt_app)

    window.ui.btn_clear_history.click()

    assert window.ui.list_history.count() == 0


# =========================
# Temas
# =========================

def test_the_window_starts_with_a_stylesheet(window):
    assert len(window.styleSheet()) > 0


def test_the_selector_lists_every_shipped_theme(window):
    combo = window.ui.combo_theme
    nombres = [combo.itemData(i) for i in range(combo.count()) if combo.itemData(i)]

    assert nombres == list(AVAILABLE_THEMES)


def test_the_selector_separates_light_from_dark(window):
    """Con nueve paletas, una lista corrida es difícil de leer."""
    combo = window.ui.combo_theme
    filas = [combo.itemData(i) for i in range(combo.count())]

    assert combo.count() == len(AVAILABLE_THEMES) + 1, "falta el separador"
    assert filas.count(None) == 1

    corte = filas.index(None)
    antes = [n for n in filas[:corte]]
    despues = [n for n in filas[corte + 1:]]

    assert all(not JsonThemeSource().load(n).is_dark for n in antes)
    assert all(JsonThemeSource().load(n).is_dark for n in despues)


def test_the_separator_cannot_be_chosen_as_a_theme(window):
    """Un separador no tiene nombre de tema; elegirlo no debe romper nada."""
    combo = window.ui.combo_theme
    corte = [combo.itemData(i) for i in range(combo.count())].index(None)
    antes = window.styleSheet()

    window._on_theme_chosen(corte)

    assert window.styleSheet() == antes


def test_the_selector_shows_readable_labels(window):
    etiquetas = [window.ui.combo_theme.itemText(i) for i in range(window.ui.combo_theme.count())]

    assert "Claro" in etiquetas
    assert "Sumi · tinta" in etiquetas
    assert "Yozora · noche" in etiquetas
    assert "washi_shu" not in etiquetas


def test_the_theme_labels_fit_the_sidebar(window):
    """
    El sidebar es angosto; una etiqueta larga se recorta con puntos y queda
    sucia. Se acota el largo en vez de descubrirlo mirando capturas.
    """
    combo = window.ui.combo_theme
    etiquetas = [combo.itemText(i) for i in range(combo.count()) if combo.itemData(i)]

    for etiqueta in etiquetas:
        assert len(etiqueta) <= 20, f"'{etiqueta}' no entra en el selector"


def test_the_selector_starts_on_the_active_theme(window):
    assert window.ui.combo_theme.currentData() == LIGHT_THEME


def test_choosing_a_theme_repaints_the_window(window):
    combo = window.ui.combo_theme
    antes = window.styleSheet()

    combo.setCurrentIndex(combo.findData("sumi"))

    assert window.styleSheet() != antes


@pytest.mark.parametrize("name", AVAILABLE_THEMES)
def test_every_theme_produces_a_stylesheet(window, name):
    combo = window.ui.combo_theme

    combo.setCurrentIndex(combo.findData(name))

    assert len(window.styleSheet()) > 0


def test_building_the_selector_does_not_save_a_preference(qt_app, tmp_path, dialogs):
    """
    Al armar el combo, setCurrentIndex emitiría el cambio y guardaría una
    preferencia que el usuario nunca eligió.
    """
    from kobun.presentation.qt.windows.main_window import MainWindow as Ventana

    prefs_path = tmp_path / "prefs.json"
    file_storage = LocalFileStorage()
    pdf_repository = PyMuPdfRepository(PdfEngineAdapter())
    pdf_service = PdfSplitterService()
    history_repository = JsonHistoryRepository(tmp_path / "datos" / "history.json")

    view_model = PdfViewModel(
        load_use_case=LoadPdfUseCase(pdf_repository, pdf_service),
        split_use_case=SplitPdfUseCase(
            pdf_repository, pdf_service, OutputPathResolver(file_storage)
        ),
        record_use_case=RecordSplitUseCase(history_repository),
        list_history_use_case=ListHistoryUseCase(history_repository, file_storage),
        file_storage=file_storage,
    )
    ventana = Ventana(
        view_model,
        ThemeService(JsonPreferencesRepository(prefs_path), JsonThemeSource()),
        history_repository,
        show_error=dialogs.show_error,
        ask_confirmation=dialogs.ask_confirmation,
    )

    try:
        assert not prefs_path.exists(), "Abrir la ventana no debe escribir preferencias"
    finally:
        ventana.close()


def test_the_chosen_theme_survives_a_new_window(qt_app, tmp_path):
    preferences = JsonPreferencesRepository(tmp_path / "preferences.json")
    service = ThemeService(preferences, JsonThemeSource())

    assert service.current().name == LIGHT_THEME
    service.select("matcha")

    otra_sesion = ThemeService(
        JsonPreferencesRepository(preferences.file_path), JsonThemeSource()
    )
    assert otra_sesion.current().name == "matcha"


# =========================
# Icono
# =========================

def test_the_window_has_an_icon(window):
    icono = window.windowIcon()

    assert not icono.isNull(), "la ventana quedaría con el icono genérico de Qt"


def test_the_icon_carries_every_declared_size(window):
    from kobun.shared.config.app_settings import APP_ICON_SIZES

    disponibles = {tamano.width() for tamano in window.windowIcon().availableSizes()}

    assert disponibles == set(APP_ICON_SIZES)


def test_the_icon_renders_at_small_sizes_without_being_empty(window):
    """
    Qt devuelve un pixmap vacío si el archivo existe pero no se pudo decodificar.
    """
    for lado in (16, 32, 48):
        pixmap = window.windowIcon().pixmap(lado, lado)

        assert not pixmap.isNull()
        assert pixmap.width() == lado


def test_the_icon_keeps_its_transparent_corners(window):
    """
    Regresión del marco negro: la esquina del pixmap debe ser transparente,
    no negra.
    """
    imagen = window.windowIcon().pixmap(64, 64).toImage()

    assert imagen.pixelColor(0, 0).alpha() == 0, "la esquina no es transparente"
    assert imagen.pixelColor(32, 32).alpha() == 255, "el centro debería ser opaco"


# =========================
# Apertura desde afuera de la ventana
# =========================

def test_open_document_loads_a_pdf_from_outside(window, qt_app, source_pdf):
    """
    Es el camino del "Abrir con" del explorador y de la línea de comandos.
    """
    window.open_document(source_pdf)
    settle(qt_app)

    assert window.ui.drop_area.label_file.text() == "libro.pdf"
    assert window.ui.split_options.label_folder.toolTip() == str(source_pdf.parent)


def test_open_document_switches_to_the_split_page(window, qt_app, source_pdf):
    """Si la app arranca en el historial, el archivo abierto no se vería."""
    window.ui.btn_history.click()
    settle(qt_app)

    window.open_document(source_pdf)
    settle(qt_app)

    assert window.ui.pages.currentIndex() == 0
    assert window.ui.btn_split.isChecked()


def test_open_document_reports_a_bad_file_like_the_drop_area(window, qt_app, dialogs, tmp_path):
    roto = tmp_path / "roto.pdf"
    roto.write_bytes(b"no soy un pdf")

    window.open_document(roto)
    settle(qt_app)

    assert len(dialogs.errors) == 1
    assert "no es un PDF" in window.ui.label_status.text()


# =========================
# Quitar una entrada del historial
# =========================

def export(window, qt_app, source_pdf, seleccion="2-4"):
    load(window, qt_app, source_pdf)
    window.ui.split_options.input_selection.setText(seleccion)
    window.ui.btn_process.click()
    settle(qt_app)


def test_forget_removes_only_the_selected_entry(window, qt_app, source_pdf):
    export(window, qt_app, source_pdf, "2-4")
    export(window, qt_app, source_pdf, "8-9")
    window.ui.btn_history.click()
    settle(qt_app)
    assert window.ui.list_history.count() == 2

    window.ui.list_history.setCurrentRow(0)
    quitado = window.ui.list_history.item(0).text()
    window.ui.btn_forget_export.click()
    settle(qt_app)

    assert window.ui.list_history.count() == 1
    assert window.ui.list_history.item(0).text() != quitado


def test_forget_does_not_delete_the_pdf(window, qt_app, source_pdf):
    """Se pierde el registro, no el archivo."""
    export(window, qt_app, source_pdf, "2-4")
    generado = source_pdf.parent / "libro_2-4.pdf"

    window.ui.btn_history.click()
    settle(qt_app)
    window.ui.list_history.setCurrentRow(0)
    window.ui.btn_forget_export.click()
    settle(qt_app)

    assert generado.exists()
    assert window.ui.list_history.count() == 0


def test_forget_asks_no_confirmation(window, qt_app, dialogs, source_pdf):
    """Sólo lo irreversible pregunta; si todo pregunta, nadie lee."""
    export(window, qt_app, source_pdf, "2-4")
    window.ui.btn_history.click()
    settle(qt_app)
    window.ui.list_history.setCurrentRow(0)

    window.ui.btn_forget_export.click()

    assert dialogs.questions == []


def test_forget_is_available_for_dead_entries_but_open_is_not(window, qt_app, source_pdf):
    """
    Es justamente el caso que motivó el botón: un archivo que ya no está y que
    antes sólo se podía sacar borrando todo el historial.
    """
    export(window, qt_app, source_pdf, "2-4")
    (source_pdf.parent / "libro_2-4.pdf").unlink()

    window.ui.btn_history.click()
    settle(qt_app)
    window.ui.list_history.setCurrentRow(0)

    assert window.ui.btn_open_export.isEnabled() is False
    assert window.ui.btn_forget_export.isEnabled() is True

    window.ui.btn_forget_export.click()
    settle(qt_app)

    assert window.ui.list_history.count() == 0


def test_forget_is_disabled_without_a_selection(window, qt_app, source_pdf):
    export(window, qt_app, source_pdf, "2-4")
    window.ui.btn_history.click()
    settle(qt_app)
    window.ui.list_history.setCurrentRow(-1)

    assert window.ui.btn_forget_export.isEnabled() is False


def test_forgetting_survives_a_reload(window, qt_app, source_pdf):
    """La eliminación se persiste, no sólo se quita de la lista en pantalla."""
    export(window, qt_app, source_pdf, "2-4")
    window.ui.btn_history.click()
    settle(qt_app)
    window.ui.list_history.setCurrentRow(0)
    window.ui.btn_forget_export.click()
    settle(qt_app)

    window._view_model.refresh_history()
    settle(qt_app)

    assert window.ui.list_history.count() == 0
