from PySide6.QtWidgets import QMessageBox, QWidget

from kobun.presentation import error_messages

CONFIRM_TITLE = "Confirmar"


def show_error(parent: QWidget, error: Exception) -> None:
    """
    Shows an error in a modal dialog.

    Used for what interrupts the user —a failed load or export— and not for
    secondary notices: those still go to the status bar, which does not demand
    a click to keep working.
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
        # Folded by default: the user can copy it for a report without having
        # to read it to understand what happened.
        box.setDetailedText(prompt.detail)

    box.exec()


def ask_confirmation(parent: QWidget, question: str, accept_text: str = "Continuar") -> bool:
    """
    Asks for confirmation before an action with no way back.

    :return: True if the user accepted.
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
