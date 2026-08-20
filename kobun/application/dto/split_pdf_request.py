from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from kobun.domain.pdf.value_objects.overwrite_policy import OverwritePolicy
from kobun.domain.pdf.value_objects.page_selection import PageSelection


@dataclass(frozen=True)
class SplitPdfRequest:
    """
    Everything needed to ask for a split.

    It exists so the UI can assemble the request in steps —the user picks a
    file, then ranges, then a destination— and hand it over as a single unit,
    instead of the use case growing loose parameters every time a new option
    shows up.
    """

    input_path: Path
    selection: PageSelection

    output_path: Optional[Path] = None
    """Destination .pdf file or existing directory. None uses the suggested
    name next to the source file."""

    policy: OverwritePolicy = OverwritePolicy.FAIL
    """What to do if the destination is already taken."""

    def __post_init__(self) -> None:
        # Normalises strings to Path so the UI can pass whatever the file dialog
        # gave it without converting by hand.
        object.__setattr__(self, "input_path", Path(self.input_path))

        if self.output_path is not None:
            object.__setattr__(self, "output_path", Path(self.output_path))
