from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from kobun.domain.pdf.exceptions.invalid_pdf_metadata_exception import InvalidPdfMetadataException


@dataclass(frozen=True, slots=True)
class PdfMetadata:
    """
    Immutable Value Object representing PDF metadata.
    """

    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[datetime] = None

    def __post_init__(self) -> None:
        self._validate_non_empty_string(self.title, "title")
        self._validate_non_empty_string(self.author, "author")
        self._validate_non_empty_string(self.subject, "subject")
        self._validate_non_empty_string(self.keywords, "keywords")
        self._validate_non_empty_string(self.creator, "creator")
        self._validate_non_empty_string(self.producer, "producer")
        self._validate_non_empty_string(self.creation_date)

    def _validate_non_empty_string(self, value: Optional[str], field_name: str) -> None:
        if value is not None and not value.strip():
            raise InvalidPdfMetadataException(
                f"{field_name.capitalize()} cannot be empty string."
            )

    def _validate_create_date(self, value: Optional[datetime]) -> None:
        if value is None:
            return

        if value.tzinfo is None:
            raise InvalidPdfMetadataException(
                "Creation date must be timezone-aware."
            )

        now = datetime.now(timezone.utc)
        if value > now:
            raise InvalidPdfMetadataException('Create date cannot be greater than current date.')

    def _validate_not_empty(self) -> None:
        if not any([self.title, self.author, self.subject, self.keywords, self.creator, self.producer]):
            raise InvalidPdfMetadataException('Metadata cannot be completely empty.')