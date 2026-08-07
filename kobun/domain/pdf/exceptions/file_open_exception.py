class FileOpenException(Exception):
    """
    No se pudo abrir un archivo con la aplicación predeterminada del sistema:
    el archivo ya no está, o el sistema no tiene con qué abrirlo.
    """

    def __init__(self, message: str):
        super().__init__(message)
