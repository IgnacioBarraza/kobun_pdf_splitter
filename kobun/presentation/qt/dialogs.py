from PySide6.QtWidgets import QMessageBox, QWidget

from kobun.presentation import error_messages

CONFIRM_TITLE = "Confirmar"


def show_error(parent: QWidget, error: Exception) -> None:
    """
    Muestra un error en un diálogo modal.

    Se usa para lo que interrumpe al usuario —una carga o una exportación que
    falló—, no para avisos secundarios: esos siguen yendo a la barra de
    estado, que no exige un clic para seguir trabajando.
    """
    prompt = error_messages.build_error_prompt(error)

    box = QMessageBox(parent)
    box.setWindowTitle(prompt.title)
    box.setText(prompt.message)
    box.setIcon(
        QMessageBox.Icon.Critical if prompt.is_critical else QMessageBox.Icon.Warning
    )
    box.setStandardButtons(QMessageBox.StandardButton.Ok)

    if prompt.detail:
        # Plegado por defecto: el usuario puede copiarlo para reportar sin
        # tener que leerlo para entender qué pasó.
        box.setDetailedText(prompt.detail)

    box.exec()


def ask_confirmation(parent: QWidget, question: str, accept_text: str = "Continuar") -> bool:
    """
    Pide confirmación antes de una acción sin vuelta atrás.

    :return: True si el usuario aceptó.
    """
    box = QMessageBox(parent)
    box.setWindowTitle(CONFIRM_TITLE)
    box.setText(question)
    box.setIcon(QMessageBox.Icon.Question)

    accept = box.addButton(accept_text, QMessageBox.ButtonRole.AcceptRole)
    box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
    box.setDefaultButton(accept)

    box.exec()

    return box.clickedButton() is accept
