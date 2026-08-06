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
    Orquesta la extracción de una selección de páginas hacia un PDF nuevo:
    valida el origen, resuelve la ruta de destino y persiste el resultado.
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
        :param request: Origen, selección de páginas, destino y política de
            sobrescritura.
        :return: Descripción completa de la operación, lista para mostrarse en
            la UI y para registrarse en el historial.
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
        Ruta que se usaría por defecto, para precargar el diálogo de guardado
        de la UI. No toca el disco ni aplica política de sobrescritura.
        """
        target_directory = directory or document.storage_path.parent
        return target_directory / self._pdf_service.suggest_output_filename(document, selection)

    def _resolve_output(self, document: PdfDocument, request: SplitPdfRequest) -> Path:
        """
        La ruta se resuelve antes de marcar el documento como PROCESSING: si el
        destino es inválido, la operación no llegó a empezar y el estado del
        documento no debe reflejar un intento fallido.
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
