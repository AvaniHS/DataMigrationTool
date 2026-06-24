"""Staging cleanup helpers for migrations and connections."""

from __future__ import annotations

from config_platform_api.connectors.payloads import LocalCsvConnectorPayload
from config_platform_api.models.migrations import MigrationRecord
from config_platform_api.storage.connection_store import ConnectionNotFoundError, ConnectionStore
from config_platform_api.storage.staging_store import StagingStore


def connection_refs_in_migration(migration: MigrationRecord) -> set[str]:
    refs: set[str] = set()
    for blueprint in migration.blueprints:
        root_ref = blueprint.sources.root_table.connection_ref.strip()
        if root_ref:
            refs.add(root_ref)
        for join in blueprint.sources.joins:
            join_ref = join.connection_ref.strip()
            if join_ref:
                refs.add(join_ref)
    return refs


def cleanup_staging_for_connection_refs(
    connection_refs: set[str],
    connection_store: ConnectionStore,
    staging_store: StagingStore,
) -> None:
    for ref in connection_refs:
        try:
            record = connection_store.get(ref)
        except ConnectionNotFoundError:
            continue
        if record.connector_id != "local_csv":
            continue
        payload = LocalCsvConnectorPayload.model_validate(record.connector_payload)
        if payload.location_kind == "platform_staging":
            staging_store.delete_connection_staging(ref)
