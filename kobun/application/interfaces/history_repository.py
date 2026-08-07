from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from kobun.domain.history.entities.export_record import ExportRecord


class HistoryRepository(ABC):
    """
    Persistencia del historial de exportaciones.

    Los registros se devuelven siempre del más reciente al más antiguo, que es
    el orden en que la UI los muestra.
    """

    @abstractmethod
    def add(self, record: ExportRecord) -> None:
        """
        Guarda una exportación. Las implementaciones pueden descartar las más
        antiguas para respetar el tope configurado.
        """
        pass

    @abstractmethod
    def list_recent(self, limit: Optional[int] = None) -> List[ExportRecord]:
        """
        :param limit: Cantidad máxima a devolver. None devuelve todo lo guardado.
        """
        pass

    @abstractmethod
    def remove(self, record_id: UUID) -> bool:
        """
        :return: True si el registro existía y se eliminó.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        pass
