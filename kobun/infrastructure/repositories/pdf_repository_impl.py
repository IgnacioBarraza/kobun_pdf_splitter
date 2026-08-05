import hashlib
from pathlib import Path
from typing import Callable, Dict, List, Optional

from pymupdf import Document

from kobun.application.interfaces.pdf_repository import PdfRepository
from kobun.domain.pdf.entities.pdf_document import PdfDocument
from kobun.domain.pdf.value_objects.page_range import PageRange
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.domain.pdf.value_objects.pdf_metadata import PdfMetadata
from kobun.infrastructure.pdf_engine.pdf_engine_adapter import PdfEngineAdapter

_CHUNK_SIZE = 4096


class PyMuPdfRepository(PdfRepository):
    """
    Implementación de PdfRepository sobre PyMuPDF, vía PdfEngineAdapter.

    Actúa como puente entre el dominio (PdfDocument, PageSelection) y el motor
    de PDFs. Todos los índices de página que recibe son 1-based.
    """

    def __init__(self, engine: PdfEngineAdapter):
        self.engine = engine

    # =========================
    # Internal Helpers
    # =========================

    def _calculate_checksum(self, file_path: Path) -> str:
        """
        Calculates SHA256 checksum of a file.

        :param file_path: Path to the file.
        :return: Hexadecimal checksum string.
        """
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(_CHUNK_SIZE), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    def _build_pdf_document(self, file_path: Path) -> PdfDocument:
        """
        Builds a PdfDocument entity from a file path.

        La metadata del archivo puede venir vacía o incompleta. Los campos
        obligatorios se completan con valores por defecto y el resto se
        normaliza a None: PdfMetadata rechaza strings vacíos, y PyMuPDF
        devuelve "" para las claves ausentes.

        `creationDate` se ignora a propósito: viene en formato PDF
        ("D:20260804120000Z") y aún no hay parser hacia datetime.
        """
        doc = self.engine.open_document(file_path)

        try:
            raw_meta = self.engine.extract_metadata(doc) or {}
            page_count = self.engine.get_page_count(doc)
        finally:
            self.engine.close_document(doc)

        domain_metadata = PdfMetadata(
            title=raw_meta.get("title") or file_path.name,
            author=raw_meta.get("author") or "Unknown",
            subject=raw_meta.get("subject") or "Unknown",
            keywords=raw_meta.get("keywords") or None,
            creator=raw_meta.get("creator") or None,
            producer=raw_meta.get("producer") or None,
        )

        return PdfDocument(
            filename=file_path.name,
            storage_path=file_path,
            metadata=domain_metadata,
            page_count=page_count,
            size_bytes=file_path.stat().st_size,
            checksum=self._calculate_checksum(file_path),
        )

    @staticmethod
    def _to_engine_metadata(metadata: PdfMetadata) -> Dict[str, Optional[str]]:
        """
        Traduce el Value Object de dominio al diccionario que espera el motor.
        """
        return {
            "title": metadata.title,
            "author": metadata.author,
            "subject": metadata.subject,
            "keywords": metadata.keywords,
            "creator": metadata.creator,
            "producer": metadata.producer,
        }

    def _export(
        self,
        source_path: Path,
        build: Callable[[Document], Document],
        output_doc: Path,
        metadata: Optional[PdfMetadata] = None,
    ) -> PdfDocument:
        """
        Ejecuta una operación de derivación (split, extract, merge) y persiste
        el resultado, garantizando que ambos documentos se cierren.

        `new_doc` se inicializa en None a propósito: si `build` falla, el
        `finally` no debe romperse con UnboundLocalError y enmascarar el
        error real del motor.
        """
        source = self.engine.open_document(source_path)
        new_doc: Optional[Document] = None

        try:
            new_doc = build(source)

            if metadata is not None:
                self.engine.set_metadata(new_doc, self._to_engine_metadata(metadata))

            self.engine.save_document(new_doc, output_doc)
        finally:
            self.engine.close_document(source)
            if new_doc is not None:
                self.engine.close_document(new_doc)

        return self._build_pdf_document(output_doc)

    # =========================
    # Repository API
    # =========================

    def open_document(self, file_path: Path) -> PdfDocument:
        if not file_path.exists():
            raise FileNotFoundError(f"No se encuentra el archivo: {file_path}")

        return self._build_pdf_document(file_path)

    def close_document(self, document: PdfDocument) -> None:
        """
        No-op for domain entity.

        Engine-level closing is handled internally.
        """
        pass

    def get_page_count(self, document: PdfDocument) -> int:
        """
        Returns the number of pages from the domain entity.
        """
        if document.page_count is None:
            raise ValueError("Page count is not initialized.")
        return document.page_count

    def extract_metadata(self, document: PdfDocument) -> PdfMetadata:
        """
        Returns metadata from the domain entity.
        """
        return document.metadata

    def extract_text(self, document: PdfDocument, page_number: int) -> str:
        """
        Extracts text from a specific page.

        :param page_number: 1-based page index.
        """
        doc = self.engine.open_document(document.storage_path)

        try:
            return self.engine.extract_text(doc, page_number)
        finally:
            self.engine.close_document(doc)

    def split_single_page(
        self,
        src_doc: PdfDocument,
        output_doc: Path,
        page_index: int
    ) -> PdfDocument:
        """
        Splits a single page into a new PDF.

        :param page_index: 1-based page index.
        """
        return self._export(
            source_path=src_doc.storage_path,
            build=lambda source: self.engine.split_single_page(source, page_index),
            output_doc=output_doc,
        )

    def split_page_range(
        self,
        src_doc: PdfDocument,
        output_doc: Path,
        page_range: PageRange
    ) -> PdfDocument:
        """
        Splits a contiguous range of pages into a new PDF.
        """
        return self._export(
            source_path=src_doc.storage_path,
            build=lambda source: self.engine.split_page_range(source, page_range),
            output_doc=output_doc,
        )

    def split_page_selection(
        self,
        src_doc: PdfDocument,
        output_doc: Path,
        selection: PageSelection,
        metadata: Optional[PdfMetadata] = None,
    ) -> PdfDocument:
        """
        Extracts a possibly discontinuous selection of ranges into a new PDF.
        """
        return self._export(
            source_path=src_doc.storage_path,
            build=lambda source: self.engine.extract_page_ranges(source, selection.ranges),
            output_doc=output_doc,
            metadata=metadata,
        )

    def merge_pdfs(
        self,
        first_doc: PdfDocument,
        second_doc: PdfDocument,
        output_doc: Path
    ) -> PdfDocument:
        """
        Merges two PDFs into a single document.
        """
        second: Optional[Document] = None

        try:
            second = self.engine.open_document(second_doc.storage_path)
            return self._export(
                source_path=first_doc.storage_path,
                build=lambda first: self.engine.merge_pdfs(first, second),
                output_doc=output_doc,
            )
        finally:
            if second is not None:
                self.engine.close_document(second)

    def extract_pages(
        self,
        document: PdfDocument,
        pages: List[int],
        output_doc: Path
    ) -> PdfDocument:
        """
        Extracts specific pages into a new PDF.

        :param pages: List of 1-based page indices.
        """
        return self._export(
            source_path=document.storage_path,
            build=lambda source: self.engine.extract_pages(source, pages),
            output_doc=output_doc,
        )
