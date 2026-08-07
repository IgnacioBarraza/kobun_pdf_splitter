from kobun.application.dto.split_pdf_response import SplitPdfResponse
from kobun.application.interfaces.history_repository import HistoryRepository
from kobun.domain.history.entities.export_record import ExportRecord


class RecordSplitUseCase:
    """
    Registra en el historial una exportación ya realizada.

    Está separado de SplitPdfUseCase a propósito: partir un PDF y llevar un
    historial son responsabilidades distintas, y el split no debería fallar
    porque el historial no se pueda escribir. La UI encadena ambos.
    """

    def __init__(self, history_repository: HistoryRepository):
        self._history_repository = history_repository

    def execute(self, response: SplitPdfResponse) -> ExportRecord:
        """
        :param response: Resultado devuelto por SplitPdfUseCase.
        :return: El registro creado, con su id ya asignado.
        """
        record = ExportRecord(
            source_path=response.source_path,
            selection=response.selection,
            output_path=response.output_path,
            page_count=response.page_count,
            size_bytes=response.output_size_bytes,
            created_at=response.completed_at,
            title=response.title,
        )

        self._history_repository.add(record)

        return record
