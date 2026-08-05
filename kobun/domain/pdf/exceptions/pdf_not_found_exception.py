from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException


class PdfNotFoundException(InvalidPdfException):
    """
    El archivo solicitado no existe.

    Hereda de InvalidPdfException para que la UI pueda capturar todos los
    errores de carga con un solo `except`, y este caso en particular sólo
    cuando quiera dar un mensaje más específico.
    """

    def __init__(self, message: str):
        super().__init__(message)
