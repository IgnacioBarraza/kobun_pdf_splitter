from pathlib import Path
from typing import Optional

from kobun.application.interfaces.pdf_repository import PdfRepository
from kobun.application.services.output_path_resolver import OutputPathResolver
from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService
from kobun.domain.pdf.value_objects.overwrite_policy import OverwritePolicy
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

    def execute(
        self,
        input_path: Path,
        selection: PageSelection,
        output_path: Optional[Path] = None,
        policy: OverwritePolicy = OverwritePolicy.FAIL,
    ) -> PdfDocument:
        """
        :param input_path: PDF de origen.
        :param selection: Páginas a extraer, 1-based (ej. "1-5,10-15").
        :param output_path: Archivo .pdf de destino, o un directorio existente
            donde escribirlo. Si se omite, se usa el nombre sugerido junto al
            archivo de origen.
        :param policy: Qué hacer si el destino ya existe. Por defecto falla.
        :return: El PdfDocument resultante, con su ruta final en `storage_path`.
        """
        document = self._pdf_repository.open_document(input_path)

        self._pdf_service.validate_selection(document, selection)
        target = self._resolve_output(document, selection, output_path, policy)

        document.mark_as_processing()

        try:
            metadata = self._pdf_service.prepare_split_metadata(document, selection)
            result = self._pdf_repository.split_page_selection(
                src_doc=document,
                output_doc=target,
                selection=selection,
                metadata=metadata,
            )

            document.mark_as_processed()
            return result

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

    def _resolve_output(
        self,
        document: PdfDocument,
        selection: PageSelection,
        output_path: Optional[Path],
        policy: OverwritePolicy,
    ) -> Path:
        """
        La ruta se resuelve antes de marcar el documento como PROCESSING: si el
        destino es inválido, la operación no llegó a empezar y el estado del
        documento no debe reflejar un intento fallido.
        """
        default_filename = self._pdf_service.suggest_output_filename(document, selection)
        requested = output_path or (document.storage_path.parent / default_filename)

        return self._output_path_resolver.resolve(
            requested=Path(requested),
            source_path=document.storage_path,
            default_filename=default_filename,
            policy=policy,
        )
