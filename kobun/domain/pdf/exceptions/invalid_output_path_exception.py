class InvalidOutputPathException(Exception):
    """
    La ruta de salida elegida no sirve: no es un .pdf, el directorio no existe
    o no es escribible, apunta al mismo archivo de origen, o ya está ocupada y
    la política vigente no permite sobrescribir.
    """

    def __init__(self, message: str):
        super().__init__(message)
