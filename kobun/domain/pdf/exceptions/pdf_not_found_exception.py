from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException


class PdfNotFoundException(InvalidPdfException):
    """
    The requested file does not exist.

    It inherits from InvalidPdfException so the UI can catch every loading
    error with a single `except`, and this case on its own only when it wants
    to give a more specific message.
    """

    def __init__(self, message: str):
        super().__init__(message)
