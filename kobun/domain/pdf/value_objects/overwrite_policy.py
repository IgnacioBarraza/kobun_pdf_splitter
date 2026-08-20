from enum import Enum


class OverwritePolicy(str, Enum):
    """
    What to do when the output file already exists.

    The system default is FAIL: exporting must never destroy an earlier file
    unless someone explicitly asked for it.
    """

    FAIL = "fail"
    """Aborts with InvalidOutputPathException."""

    OVERWRITE = "overwrite"
    """Replaces the existing file."""

    RENAME = "rename"
    """Looks for the first free name: book_1.pdf, book_2.pdf, ..."""
