from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException
from kobun.domain.pdf.value_objects.page_range import PageRange

_SEPARATORS = (";", " ", "\t", "\n")


@dataclass(frozen=True, slots=True)
class PageSelection:
    """
    Value Object inmutable que representa la selección completa de páginas
    pedida por el usuario: uno o más rangos, por ejemplo "1-5,10-15,20".

    La selección se guarda siempre en forma canónica: los rangos quedan
    ordenados y los solapados o contiguos fusionados. Eso hace que dos
    selecciones que representan el mismo conjunto de páginas sean iguales
    ("1-5,3-8" == "1-8") y que la extracción nunca duplique una página.
    """
    ranges: Tuple[PageRange, ...]

    def __post_init__(self) -> None:
        if not self.ranges:
            raise InvalidPageRangeException("A page selection must contain at least one range.")

        object.__setattr__(self, "ranges", self._canonicalize(self.ranges))

    @staticmethod
    def _canonicalize(ranges: Sequence[PageRange]) -> Tuple[PageRange, ...]:
        ordered = sorted(ranges, key=lambda r: (r.start, r.end))

        merged: List[PageRange] = [ordered[0]]
        for current in ordered[1:]:
            if merged[-1].overlaps_or_touches(current):
                merged[-1] = merged[-1].merge(current)
            else:
                merged.append(current)

        return tuple(merged)

    @classmethod
    def parse(cls, text: str) -> "PageSelection":
        """
        Construye una selección desde texto: "1-5,10-15", "7", "1-3; 8".

        Acepta coma, punto y coma o espacios como separadores.

        :raises InvalidPageRangeException: Si el texto está vacío o algún rango es inválido.
        """
        normalized = text.strip()
        for separator in _SEPARATORS:
            normalized = normalized.replace(separator, ",")

        chunks = [chunk for chunk in normalized.split(",") if chunk]
        if not chunks:
            raise InvalidPageRangeException("Page selection cannot be empty.")

        return cls(ranges=tuple(PageRange.parse(chunk) for chunk in chunks))

    @classmethod
    def of(cls, *ranges: PageRange) -> "PageSelection":
        """Azúcar sintáctico para construir una selección desde rangos ya validados."""
        return cls(ranges=tuple(ranges))

    @property
    def max_page(self) -> int:
        """Página más alta solicitada. Se usa para validar contra el total del documento."""
        return self.ranges[-1].end

    @property
    def min_page(self) -> int:
        return self.ranges[0].start

    @property
    def total_pages(self) -> int:
        """Cantidad real de páginas a extraer, sin duplicados."""
        return sum(r.total_pages for r in self.ranges)

    @property
    def is_contiguous(self) -> bool:
        return len(self.ranges) == 1

    def to_pages(self) -> List[int]:
        """
        Lista de páginas 1-based, ordenada y sin duplicados.
        """
        pages: List[int] = []
        for p_range in self.ranges:
            pages.extend(p_range.to_range())
        return pages

    def __iter__(self) -> Iterable[PageRange]:
        return iter(self.ranges)

    def __len__(self) -> int:
        return len(self.ranges)

    def __str__(self) -> str:
        return ",".join(str(r) for r in self.ranges)
