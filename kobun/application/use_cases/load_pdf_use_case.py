from pathlib import Path

from kobun.application.interfaces.pdf_repository import PdfRepository
from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.services.pdf_splitter_service import PdfSplitterService


class LoadPdfUseCase:
    """
    Abre un PDF y garantiza que sea utilizable, para que la UI pueda mostrar
    su nombre, cantidad de páginas y metadata antes de pedir un rango.

    Es el único punto de entrada para cargar un archivo: tanto el botón de
    "seleccionar archivo" como el drag & drop deben pasar por aquí, porque es
    donde se rechazan los archivos que no son PDFs legibles.
    """

    def __init__(self, pdf_repository: PdfRepository, pdf_service: PdfSplitterService):
        self._pdf_repository = pdf_repository
        self._pdf_service = pdf_service

    def execute(self, file_path: Path) -> PdfDocument:
        """
        :param file_path: Ruta del PDF a cargar.
        :return: El documento validado y listo para dividirse.
        :raises PdfNotFoundException: Si la ruta no existe.
        :raises EncryptedPdfException: Si el PDF pide contraseña.
        :raises InvalidPdfException: Si no es un PDF legible o no tiene páginas.
        """
        document = self._pdf_repository.open_document(Path(file_path))
        self._pdf_service.validate_document_for_processing(document)

        return document
