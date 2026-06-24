"""Persist migration drafts for P2 (JSON file)."""

import json
from datetime import UTC, datetime
from pathlib import Path

from config_platform_api.exceptions import MigrationStoreError
from config_platform_api.logging_setup import get_logger
from config_platform_api.models.migrations import (
    Blueprint,
    CreateMigrationRequest,
    MigrationListItem,
    MigrationRecord,
    UpdateMigrationRequest,
)
from config_platform_api.services.migration_factory import (
    create_empty_blueprint,
    duplicate_blueprint,
    next_sequence_order,
    normalize_blueprint_sequence,
)

logger = get_logger(__name__)


class MigrationNotFoundError(LookupError):
    """Raised when a migration id does not exist."""


class MigrationAlreadyExistsError(ValueError):
    """Raised when creating a duplicate migration id."""


class BlueprintNotFoundError(LookupError):
    """Raised when a blueprint sequence_order does not exist."""


class MigrationStore:
    def __init__(self, storage_path: Path) -> None:
        self._storage_path = storage_path
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._storage_path.exists():
            self._write({})

    def list_items(self) -> list[MigrationListItem]:
        records = self._read_all()
        return [
            MigrationListItem(
                migration_id=record.migration_id,
                client_id=record.client_id,
                version=record.version,
                output_format=record.output_format,
                blueprint_count=len(record.blueprints),
                updated_at=record.updated_at,
            )
            for record in sorted(records.values(), key=lambda item: item.migration_id)
        ]

    def get(self, migration_id: str) -> MigrationRecord:
        record = self._read_all().get(migration_id)
        if record is None:
            raise MigrationNotFoundError(f"Migration '{migration_id}' was not found.")
        return record

    def create(self, request: CreateMigrationRequest) -> MigrationRecord:
        records = self._read_all()
        if request.migration_id in records:
            raise MigrationAlreadyExistsError(f"Migration '{request.migration_id}' already exists.")
        now = datetime.now(UTC)
        record = MigrationRecord(
            migration_id=request.migration_id,
            client_id=request.client_id,
            version=request.version,
            output_format=request.output_format,
            blueprints=[],
            created_at=now,
            updated_at=now,
        )
        records[request.migration_id] = record
        self._write(records)
        logger.info("migration_created", migration_id=request.migration_id)
        return record

    def update(self, migration_id: str, request: UpdateMigrationRequest) -> MigrationRecord:
        records = self._read_all()
        existing = records.get(migration_id)
        if existing is None:
            raise MigrationNotFoundError(f"Migration '{migration_id}' was not found.")
        updated = existing.model_copy(
            update={
                "client_id": request.client_id,
                "version": request.version,
                "blueprints": normalize_blueprint_sequence(request.blueprints),
                "updated_at": datetime.now(UTC),
            },
        )
        records[migration_id] = updated
        self._write(records)
        logger.info("migration_updated", migration_id=migration_id)
        return updated

    def delete(self, migration_id: str) -> None:
        records = self._read_all()
        if migration_id not in records:
            raise MigrationNotFoundError(f"Migration '{migration_id}' was not found.")
        del records[migration_id]
        self._write(records)
        logger.info("migration_deleted", migration_id=migration_id)

    def add_blueprint(self, migration_id: str) -> MigrationRecord:
        records = self._read_all()
        existing = records.get(migration_id)
        if existing is None:
            raise MigrationNotFoundError(f"Migration '{migration_id}' was not found.")
        sequence_order = next_sequence_order(existing.blueprints)
        blueprints = [*existing.blueprints, create_empty_blueprint(sequence_order)]
        return self._save_blueprints(records, migration_id, existing, blueprints)

    def delete_blueprint(self, migration_id: str, sequence_order: int) -> MigrationRecord:
        records = self._read_all()
        existing = records.get(migration_id)
        if existing is None:
            raise MigrationNotFoundError(f"Migration '{migration_id}' was not found.")
        blueprints = [bp for bp in existing.blueprints if bp.sequence_order != sequence_order]
        if len(blueprints) == len(existing.blueprints):
            raise BlueprintNotFoundError(
                f"Blueprint sequence_order {sequence_order} was not found.",
            )
        return self._save_blueprints(
            records,
            migration_id,
            existing,
            normalize_blueprint_sequence(blueprints),
        )

    def duplicate_blueprint(self, migration_id: str, sequence_order: int) -> MigrationRecord:
        records = self._read_all()
        existing = records.get(migration_id)
        if existing is None:
            raise MigrationNotFoundError(f"Migration '{migration_id}' was not found.")
        source = next(
            (bp for bp in existing.blueprints if bp.sequence_order == sequence_order),
            None,
        )
        if source is None:
            raise BlueprintNotFoundError(
                f"Blueprint sequence_order {sequence_order} was not found.",
            )
        new_order = next_sequence_order(existing.blueprints)
        blueprints = [*existing.blueprints, duplicate_blueprint(source, new_order)]
        return self._save_blueprints(records, migration_id, existing, blueprints)

    def reorder_blueprints(self, migration_id: str, sequence_orders: list[int]) -> MigrationRecord:
        records = self._read_all()
        existing = records.get(migration_id)
        if existing is None:
            raise MigrationNotFoundError(f"Migration '{migration_id}' was not found.")
        by_order = {bp.sequence_order: bp for bp in existing.blueprints}
        if set(sequence_orders) != set(by_order):
            raise ValueError("sequence_orders must include each blueprint exactly once.")
        reordered = [by_order[order] for order in sequence_orders]
        return self._save_blueprints(
            records,
            migration_id,
            existing,
            normalize_blueprint_sequence(reordered),
        )

    def _save_blueprints(
        self,
        records: dict[str, MigrationRecord],
        migration_id: str,
        existing: MigrationRecord,
        blueprints: list[Blueprint],
    ) -> MigrationRecord:
        updated = existing.model_copy(
            update={"blueprints": blueprints, "updated_at": datetime.now(UTC)},
        )
        records[migration_id] = updated
        self._write(records)
        logger.info("migration_blueprints_updated", migration_id=migration_id)
        return updated

    def _read_all(self) -> dict[str, MigrationRecord]:
        try:
            raw = json.loads(self._storage_path.read_text(encoding="utf-8"))
            return {
                migration_id: MigrationRecord.model_validate(payload)
                for migration_id, payload in raw.items()
            }
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            logger.error(
                "migration_store_read_failed",
                path=str(self._storage_path),
                error_type=type(exc).__name__,
            )
            raise MigrationStoreError("Migration registry is unavailable.") from exc

    def _write(self, records: dict[str, MigrationRecord]) -> None:
        payload = {
            migration_id: record.model_dump(mode="json")
            for migration_id, record in records.items()
        }
        try:
            self._storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError as exc:
            logger.error(
                "migration_store_write_failed",
                path=str(self._storage_path),
                error_type=type(exc).__name__,
            )
            raise MigrationStoreError("Migration registry is unavailable.") from exc
