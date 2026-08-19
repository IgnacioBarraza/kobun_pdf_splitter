class InvalidExportRecordException(Exception):
    """
    El registro de exportación no cumple sus invariantes: le falta origen o
    destino, no tiene páginas, o la fecha no es utilizable.
    """

    def __init__(self, message: str):
        super().__init__(message)
