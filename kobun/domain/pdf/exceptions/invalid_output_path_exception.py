class InvalidOutputPathException(Exception):
    """
    The chosen output path is unusable: it is not a .pdf, the directory does
    not exist or is not writable, it points at the source file itself, or it is
    already taken and the current policy does not allow overwriting.
    """

    def __init__(self, message: str):
        super().__init__(message)
