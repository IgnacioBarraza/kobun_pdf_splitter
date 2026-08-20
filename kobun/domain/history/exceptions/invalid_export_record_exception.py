class InvalidExportRecordException(Exception):
    """
    The export record breaks its invariants: it is missing a source or a
    destination, has no pages, or its date is unusable.
    """

    def __init__(self, message: str):
        super().__init__(message)
