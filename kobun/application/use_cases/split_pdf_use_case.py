from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from kobun.application.dto.split_pdf_request import SplitPdfRequest
from kobun.application.dto.split_pdf_response import SplitPdfResponse
from kobun.application.interfaces.pdf_repository import PdfRepository
from kobun.application.services.output_path_resolver import OutputPathResolver
from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService
from kobun.domain.pdf.value_objects.page_selection import PageSelection


class SplitPdfUseCase:
    """
    Orchestrates extracting a page selection into a new PDF: validates the
    source, resolves the destination path and persists the result.
    """

    def __init__(
        self,
        pdf_repository: PdfRepository,
        pdf_service: PdfSplitterService,
        output_path_resolver: OutputPathResolver,
    ):
        self._pdf_repository = pdf_repository
        self._pdf_service = pdf_service
        self._output_path_resolver = output_path_resolver

    def execute(self, request: SplitPdfRequest) -> SplitPdfResponse:
        """
        :param request: Source, page selection, destination and overwrite
            policy.
        :return: A full description of the operation, ready to be shown in the
            UI and recorded in the history.
        """
        document = self._pdf_repository.open_document(request.input_path)

        self._pdf_service.validate_selection(document, request.selection)
        target = self._resolve_output(document, request)

        document.mark_as_processing()

        try:
            metadata = self._pdf_service.prepare_split_metadata(document, request.selection)
            result = self._pdf_repository.split_page_selection(
                src_doc=document,
                output_doc=target,
                selection=request.selection,
                metadata=metadata,
            )

            document.mark_as_processed()
            return self._build_response(document, result, request.selection)

        except Exception:
            document.mark_as_failed()
            raise

    def suggest_output_path(
        self,
        document: PdfDocument,
        selection: PageSelection,
        directory: Optional[Path] = None,
    ) -> Path:
        """
        The path that would be used by default, to prefill the UI's save
        dialog. It touches no disk and applies no overwrite policy.
        """
        target_directory = directory or document.storage_path.parent
        return target_directory / self._pdf_service.suggest_output_filename(document, selection)

    def _resolve_output(self, document: PdfDocument, request: SplitPdfRequest) -> Path:
        """
        The path is resolved before marking the document as PROCESSING: if the
        destination is invalid the operation never started, and the document's
        state must not reflect a failed attempt.
        """
        default_filename = self._pdf_service.suggest_output_filename(document, request.selection)
        requested = request.output_path or (document.storage_path.parent / default_filename)

        return self._output_path_resolver.resolve(
            requested=requested,
            source_path=document.storage_path,
            default_filename=default_filename,
            policy=request.policy,
        )

    @staticmethod
    def _build_response(
        source: PdfDocument,
        result: PdfDocument,
        selection: PageSelection,
    ) -> SplitPdfResponse:
        return SplitPdfResponse(
            source_path=source.storage_path,
            selection=selection,
            output_path=result.storage_path,
            output_size_bytes=result.size_bytes,
            page_count=result.page_count,
            completed_at=datetime.now(timezone.utc),
            title=result.metadata.title,
        )
