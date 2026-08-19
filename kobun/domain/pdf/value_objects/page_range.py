from dataclasses import dataclass

from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException

# Guiones que suelen aparecer al copiar rangos desde un PDF o un navegador.
_DASHES = ("–", "—", "−")


@dataclass(frozen=True)
class PageRange:
    """
    Rango contiguo de páginas, en numeración 1-based e inclusiva en ambos extremos.
    """
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start <= 0 or self.end <= 0:
            raise InvalidPageRangeException(f"Invalid page range: {self.start}-{self.end}")
        if self.start > self.end:
            raise InvalidPageRangeException(f"Start page {self.start} cannot be greater than end page {self.end}")

    @classmethod
    def parse(cls, text: str) -> "PageRange":
        """
        Construye un rango desde texto: "12" (página suelta) o "1-5".

        :raises InvalidPageRangeException: Si el texto no es un rango válido.
        """
        raw = text.strip()
        for dash in _DASHES:
            raw = raw.replace(dash, "-")

        if not raw:
            raise InvalidPageRangeException("Page range cannot be empty.")

        parts = raw.split("-")

        if len(parts) == 1:
            page = cls._parse_page(parts[0], raw)
            return cls(start=page, end=page)

        if len(parts) == 2:
            return cls(
                start=cls._parse_page(parts[0], raw),
                end=cls._parse_page(parts[1], raw),
            )

        raise InvalidPageRangeException(f"Invalid page range format: '{text}'. Expected '5' or '1-5'.")

    @staticmethod
    def _parse_page(value: str, original: str) -> int:
        stripped = value.strip()
        if not stripped.isdigit():
            raise InvalidPageRangeException(f"Invalid page number '{stripped}' in range '{original}'.")
        return int(stripped)

    @property
    def total_pages(self) -> int:
        return self.end - self.start + 1

    def contains(self, page: int) -> bool:
        return self.start <= page <= self.end

    def overlaps_or_touches(self, other: "PageRange") -> bool:
        """
        True si ambos rangos se solapan o son contiguos (1-5 y 6-10), es decir,
        si pueden fusionarse sin alterar el conjunto de páginas resultante.
        """
        return self.start <= other.end + 1 and other.start <= self.end + 1

    def merge(self, other: "PageRange") -> "PageRange":
        """
        Fusiona dos rangos solapados o contiguos en uno solo.

        :raises InvalidPageRangeException: Si los rangos son disjuntos.
        """
        if not self.overlaps_or_touches(other):
            raise InvalidPageRangeException(f"Cannot merge disjoint ranges: {self} and {other}.")
        return PageRange(start=min(self.start, other.start), end=max(self.end, other.end))

    def __str__(self) -> str:
        if self.start == self.end:
            return str(self.start)
        return f"{self.start}-{self.end}"

    def to_range(self) -> range:
        return range(self.start, self.end + 1)
