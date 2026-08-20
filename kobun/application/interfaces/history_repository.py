from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from kobun.domain.history.entities.export_record import ExportRecord


class HistoryRepository(ABC):
    """
    Persistence of the export history.

    Records always come back newest first, which is the order the UI shows
    them in.
    """

    @abstractmethod
    def add(self, record: ExportRecord) -> None:
        """
        Stores an export. Implementations may drop the oldest ones to respect
        the configured cap.
        """
        pass

    @abstractmethod
    def list_recent(self, limit: Optional[int] = None) -> List[ExportRecord]:
        """
        :param limit: Maximum number to return. None returns everything stored.
        """
        pass

    @abstractmethod
    def remove(self, record_id: UUID) -> bool:
        """
        :return: True if the record existed and was removed.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        pass
