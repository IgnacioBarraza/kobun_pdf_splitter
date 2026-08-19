from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException


class EncryptedPdfException(InvalidPdfException):
    """
    El PDF está protegido con contraseña y no puede leerse.

    Es un caso frecuente en libros y papers, y merece un mensaje propio en la
    UI: no es un archivo corrupto, simplemente falta la clave.
    """

    def __init__(self, message: str):
        super().__init__(message)
