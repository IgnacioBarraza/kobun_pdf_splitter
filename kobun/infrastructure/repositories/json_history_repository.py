import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from kobun.application.interfaces.history_repository import HistoryRepository
from kobun.domain.history.entities.export_record import ExportRecord
from kobun.domain.pdf.value_objects.page_selection import PageSelection
from kobun.shared.config.app_settings import MAX_HISTORY_ENTRIES

SCHEMA_VERSION = 1


class JsonHistoryRepository(HistoryRepository):
    """
    Historial persistido en un único archivo JSON.

    Tres decisiones que importan:

    - **Escritura atómica**: se escribe a un temporal y se reemplaza. Si la app
      muere a mitad de guardar, el historial anterior queda intacto en vez de
      convertirse en un archivo truncado.
    - **Tolerancia a corrupción**: el historial es conveniencia, no datos
      críticos. Un JSON ilegible se aparta con extensión `.corrupt` y se
      empieza de cero, en lugar de impedir que la aplicación arranque.
    - **Tolerancia por entrada**: un registro con formato inválido se descarta
      solo, sin arrastrar al resto de la lista.
    """

    def __init__(self, file_path: Path, max_entries: int = MAX_HISTORY_ENTRIES):
        self._file_path = Path(file_path)
        self._max_entries = max_entries

    @property
    def file_path(self) -> Path:
        return self._file_path

    def add(self, record: ExportRecord) -> None:
        records = self._read_all()
        records.insert(0, record)

        self._write_all(records[: self._max_entries])

    def list_recent(self, limit: Optional[int] = None) -> List[ExportRecord]:
        records = self._read_all()

        return records if limit is None else records[:limit]

    def remove(self, record_id: UUID) -> bool:
        records = self._read_all()
        remaining = [record for record in records if record.id != record_id]

        if len(remaining) == len(records):
            return False

        self._write_all(remaining)
        return True

    def clear(self) -> None:
        self._file_path.unlink(missing_ok=True)

    # =========================
    # Persistencia
    # =========================

    def _read_all(self) -> List[ExportRecord]:
        if not self._file_path.exists():
            return []

        try:
            with open(self._file_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            self._quarantine()
            return []

        entries = payload.get("entries", []) if isinstance(payload, dict) else []

        records = []
        for entry in entries:
            record = self._deserialize(entry)
            if record is not None:
                records.append(record)

        return records

    def _write_all(self, records: List[ExportRecord]) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "version": SCHEMA_VERSION,
            "entries": [self._serialize(record) for record in records],
        }

        # Temporal en el mismo directorio: os.replace sólo es atómico dentro
        # del mismo sistema de archivos.
        temporary = self._file_path.with_name(f"{self._file_path.name}.tmp")

        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

        os.replace(temporary, self._file_path)

    def _quarantine(self) -> None:
        """
        Aparta un historial ilegible en vez de borrarlo, por si alguien quiere
        recuperarlo a mano.
        """
        try:
            self._file_path.replace(self._file_path.with_name(f"{self._file_path.name}.corrupt"))
        except OSError:
            pass

    # =========================
    # Mapeo
    # =========================

    @staticmethod
    def _serialize(record: ExportRecord) -> Dict[str, Any]:
        return {
            "id": str(record.id),
            "source_path": str(record.source_path),
            "selection": str(record.selection),
            "output_path": str(record.output_path),
            "page_count": record.page_count,
            "size_bytes": record.size_bytes,
            "created_at": record.created_at.isoformat(),
            "title": record.title,
        }

    @staticmethod
    def _deserialize(entry: Any) -> Optional[ExportRecord]:
        if not isinstance(entry, dict):
            return None

        try:
            return ExportRecord(
                id=UUID(entry["id"]),
                source_path=Path(entry["source_path"]),
                selection=PageSelection.parse(entry["selection"]),
                output_path=Path(entry["output_path"]),
                page_count=int(entry["page_count"]),
                size_bytes=int(entry["size_bytes"]),
                created_at=datetime.fromisoformat(entry["created_at"]),
                title=entry.get("title"),
            )
        except Exception:
            # Una entrada rota no debe impedir leer las demás.
            return None
