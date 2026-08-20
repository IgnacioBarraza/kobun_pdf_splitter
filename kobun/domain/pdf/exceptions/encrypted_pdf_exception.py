from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException


class EncryptedPdfException(InvalidPdfException):
    """
    The PDF is password protected and cannot be read.

    A common case with books and papers, and it deserves its own message in the
    UI: the file is not corrupt, the key is simply missing.
    """

    def __init__(self, message: str):
        super().__init__(message)
