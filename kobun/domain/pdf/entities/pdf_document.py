from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import uuid4, UUID

from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException
from kobun.domain.pdf.value_objects.pdf_metadata import PdfMetadata


class PdfProcessingStatus(str, Enum):
    """Represents the processing lifecycle of a PDF document."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


@dataclass(eq=False, slots=True)
class PdfDocument:
    filename: str = field(init=True)
    storage_path: Path = field(init=True)
    size_bytes: int = field(init=True)
    checksum: str = field(init=True)
    metadata: PdfMetadata

    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None
    page_count: Optional[int] = None
    status: PdfProcessingStatus = PdfProcessingStatus.UPLOADED
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        """
        Ensures domain invariants at creation time.
        """
        if not self.filename.endswith(".pdf"):
            raise InvalidPdfException("Filename must end with .pdf")

        if self.size_bytes <= 0:
            raise InvalidPdfException("File size must be greater than zero.")

        if not self.checksum:
            raise InvalidPdfException("Checksum cannot be empty.")


    def mark_as_processing(self) -> None:
        """
        Marks the document as currently being processed.
        """
        if self.status != PdfProcessingStatus.UPLOADED:
            raise InvalidPdfException("Only uploaded documents can start processing.")
        self.status = PdfProcessingStatus.PROCESSING

    def mark_as_processed(self, page_count: int) -> None:
        """
        Marks the document as successfully processed.

        :param page_count: Total number of pages detected.
        """
        if self.status != PdfProcessingStatus.PROCESSING:
            raise InvalidPdfException("Document must be processing before marking as processed.")

        self.status = PdfProcessingStatus.PROCESSED
        self.page_count = page_count
        self.processed_at = datetime.now(timezone.utc)

    def mark_as_failed(self) -> None:
        """
        Marks the document as failed during processing.
        """
        self.status = PdfProcessingStatus.FAILED

    def rename(self, new_filename: str) -> None:
        """
        Business rule for renaming a document.
        """
        if not new_filename.lower().endswith(".pdf"):
            raise InvalidPdfException("Filename must end with .pdf")
        self.filename = new_filename

    def __eq__(self, other: object) -> bool:
        """
        Equality based solely on identity.
        """
        if isinstance(other, PdfDocument):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        """
        Hash based on identity.
        """
        return hash(self.id)