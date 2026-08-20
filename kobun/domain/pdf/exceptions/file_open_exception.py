class FileOpenException(Exception):
    """
    A file could not be opened with the system's default application: the
    file is gone, or the system has nothing to open it with.
    """

    def __init__(self, message: str):
        super().__init__(message)
