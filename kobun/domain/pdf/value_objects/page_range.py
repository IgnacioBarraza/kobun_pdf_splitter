from dataclasses import dataclass
from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException

@dataclass(frozen=True)
class PageRange:
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start <= 0 or self.end <= 0:
            raise InvalidPageRangeException(f"Invalid page range: {self.start}-{self.end}")
        if self.start > self.end:
            raise InvalidPageRangeException(f"Start page {self.start} cannot be greater than end page {self.end}")

    @property
    def total_pages(self) -> int:
        return self.end - self.start + 1

    def __str__(self):
        return f"{self.start}-{self.end}"

    def to_range(self):
        return range(self.start, self.end + 1)