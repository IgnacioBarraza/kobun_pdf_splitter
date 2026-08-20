from kobun.application.dto.split_pdf_response import SplitPdfResponse
from kobun.application.interfaces.history_repository import HistoryRepository
from kobun.domain.history.entities.export_record import ExportRecord


class RecordSplitUseCase:
    """
    Records an export that already happened into the history.

    Separated from SplitPdfUseCase on purpose: splitting a PDF and keeping a
    history are different responsibilities, and the split should not fail
    because the history cannot be written. The UI chains the two.
    """

    def __init__(self, history_repository: HistoryRepository):
        self._history_repository = history_repository

    def execute(self, response: SplitPdfResponse) -> ExportRecord:
        """
        :param response: The result returned by SplitPdfUseCase.
        :return: The created record, with its id already assigned.
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
