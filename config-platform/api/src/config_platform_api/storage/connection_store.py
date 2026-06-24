"""Persist connection registry (JSON file)."""

import json
from datetime import UTC, datetime
from pathlib import Path

from config_platform_api.connectors.legacy import migrate_legacy_connection_record
from config_platform_api.connectors.registry import connector_registry
from config_platform_api.exceptions import ConnectionStoreError
from config_platform_api.logging_setup import get_logger
from config_platform_api.models.connections import ConnectionListItem, ConnectionRecord, ConnectionSaveRequest
from config_platform_api.services.connection_builder import build_connection_summary, validate_connection_payload

logger = get_logger(__name__)


class ConnectionNotFoundError(LookupError):
    """Raised when a connection ref does not exist."""


class ConnectionAlreadyExistsError(ValueError):
    """Raised when creating a duplicate connection ref."""


class ConnectionStore:
    def __init__(self, storage_path: Path) -> None:
        self._storage_path = storage_path
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._storage_path.exists():
            self._write({})

    def list_items(self) -> list[ConnectionListItem]:
        records = self._read_all()
        items: list[ConnectionListItem] = []
        for record in sorted(records.values(), key=lambda item: item.ref):
            connector = connector_registry.get(record.connector_id)
            metadata = connector.metadata()
            items.append(
                ConnectionListItem(
                    ref=record.ref,
                    connector_id=record.connector_id,
                    export_type=metadata.export_type,
                    category=metadata.category,
                    summary=build_connection_summary(record),
                    last_tested_at=record.last_tested_at,
                    updated_at=record.updated_at,
                ),
            )
        return items

    def get(self, ref: str) -> ConnectionRecord:
        record = self._read_all().get(ref)
        if record is None:
            raise ConnectionNotFoundError(f"Connection '{ref}' was not found.")
        return record

    def create(self, request: ConnectionSaveRequest, *, tested_at: datetime) -> ConnectionRecord:
        validate_connection_payload(request)
        records = self._read_all()
        if request.ref in records:
            raise ConnectionAlreadyExistsError(f"Connection '{request.ref}' already exists.")
        now = datetime.now(UTC)
        record = ConnectionRecord(
            **request.model_dump(exclude={"verification_token"}),
            created_at=now,
            updated_at=now,
            last_tested_at=tested_at,
        )
        records[request.ref] = record
        self._write(records)
        logger.info("connection_created", ref=request.ref, connector_id=request.connector_id)
        return record

    def update(self, ref: str, request: ConnectionSaveRequest, *, tested_at: datetime) -> ConnectionRecord:
        validate_connection_payload(request)
        if ref != request.ref:
            raise ValueError("Connection ref in path and body must match.")
        records = self._read_all()
        existing = records.get(ref)
        if existing is None:
            raise ConnectionNotFoundError(f"Connection '{ref}' was not found.")
        updated = existing.model_copy(
            update={
                "connector_id": request.connector_id,
                "connector_payload": request.connector_payload,
                "secret_ref": request.secret_ref,
                "updated_at": datetime.now(UTC),
                "last_tested_at": tested_at,
            },
        )
        records[ref] = updated
        self._write(records)
        logger.info("connection_updated", ref=request.ref, connector_id=request.connector_id)
        return updated

    def delete(self, ref: str) -> None:
        records = self._read_all()
        if ref not in records:
            raise ConnectionNotFoundError(f"Connection '{ref}' was not found.")
        del records[ref]
        self._write(records)
        logger.info("connection_deleted", ref=ref)

    def export_all(self) -> dict[str, dict[str, object]]:
        from config_platform_api.services.connection_builder import record_to_export_dict

        return {ref: record_to_export_dict(record) for ref, record in self._read_all().items()}

    def _read_all(self) -> dict[str, ConnectionRecord]:
        try:
            raw = json.loads(self._storage_path.read_text(encoding="utf-8"))
            records: dict[str, ConnectionRecord] = {}
            for ref, payload in raw.items():
                migrated = migrate_legacy_connection_record(payload)
                records[ref] = ConnectionRecord.model_validate(migrated)
            return records
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            logger.error(
                "connection_store_read_failed",
                path=str(self._storage_path),
                error_type=type(exc).__name__,
            )
            raise ConnectionStoreError("Connection registry is unavailable.") from exc

    def _write(self, records: dict[str, ConnectionRecord]) -> None:
        payload = {ref: record.model_dump(mode="json") for ref, record in records.items()}
        try:
            self._storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError as exc:
            logger.error(
                "connection_store_write_failed",
                path=str(self._storage_path),
                error_type=type(exc).__name__,
            )
            raise ConnectionStoreError("Connection registry is unavailable.") from exc
