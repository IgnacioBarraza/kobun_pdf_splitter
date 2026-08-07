from typing import List, Optional

from kobun.application.dto.history_entry import HistoryEntry
from kobun.application.interfaces.file_storage import FileStorage
from kobun.application.interfaces.history_repository import HistoryRepository


class ListHistoryUseCase:
    """
    Devuelve el historial de exportaciones, marcando cuáles siguen existiendo
    en disco.

    Las entradas cuyo archivo desapareció no se filtran: se marcan. Borrarlas
    en silencio confundiría al usuario, que recuerda haber exportado ese
    archivo; verlo en gris le dice qué pasó y le deja decidir.
    """

    def __init__(self, history_repository: HistoryRepository, file_storage: FileStorage):
        self._history_repository = history_repository
        self._file_storage = file_storage

    def execute(self, limit: Optional[int] = None) -> List[HistoryEntry]:
        """
        :param limit: Cantidad máxima de entradas, de la más reciente a la más
            antigua. None devuelve todas.
        """
        records = self._history_repository.list_recent(limit)

        return [
            HistoryEntry(
                record=record,
                is_available=self._file_storage.is_file(record.output_path),
            )
            for record in records
        ]
