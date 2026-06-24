"""Assemble contract-shaped migration export JSON."""

from __future__ import annotations

from typing import Any

from config_platform_api.models.migrations import Blueprint, MigrationRecord
from config_platform_api.services.connection_builder import record_to_export_dict
from config_platform_api.storage.connection_store import ConnectionNotFoundError, ConnectionStore


class MigrationExportError(ValueError):
    """Raised when a migration cannot be exported."""


def collect_connection_refs(migration: MigrationRecord) -> set[str]:
    refs: set[str] = set()
    for blueprint in migration.blueprints:
        target_ref = blueprint.target.connection_ref.strip()
        if target_ref:
            refs.add(target_ref)
        root_ref = blueprint.sources.root_table.connection_ref.strip()
        if root_ref:
            refs.add(root_ref)
        for join in blueprint.sources.joins:
            join_ref = join.connection_ref.strip()
            if join_ref:
                refs.add(join_ref)
    return refs


def assemble_migration_export(
    migration: MigrationRecord,
    connection_store: ConnectionStore,
) -> dict[str, Any]:
    connection_refs = collect_connection_refs(migration)
    connections: dict[str, dict[str, Any]] = {}
    for ref in sorted(connection_refs):
        try:
            record = connection_store.get(ref)
        except ConnectionNotFoundError as exc:
            raise MigrationExportError(
                f"Blueprint references missing connection '{ref}'. Save the connection under Connect first.",
            ) from exc
        connections[ref] = record_to_export_dict(record)

    blueprints = [
        blueprint_to_export_dict(blueprint)
        for blueprint in sorted(migration.blueprints, key=lambda item: item.sequence_order)
    ]

    return {
        "migration_id": migration.migration_id,
        "client_id": migration.client_id,
        "version": migration.version,
        "output_format": migration.output_format,
        "connections": connections,
        "blueprints": blueprints,
    }


def blueprint_to_export_dict(blueprint: Blueprint) -> dict[str, Any]:
    payload = blueprint.model_dump(by_alias=True, mode="json", exclude_none=True)
    _normalize_sources(payload.get("sources", {}))
    _strip_empty_strings(payload)
    return payload


def _normalize_sources(sources: dict[str, Any]) -> None:
    root = sources.get("root_table")
    if isinstance(root, dict):
        _normalize_file_source(root)
    joins = sources.get("joins")
    if isinstance(joins, list):
        for join in joins:
            if isinstance(join, dict):
                _normalize_file_source(join)


def _normalize_file_source(source: dict[str, Any]) -> None:
    file_name = source.get("file_name")
    if file_name:
        source.pop("schema", None)
        source.pop("table_name", None)
    else:
        source.pop("file_name", None)


def _strip_empty_strings(node: Any) -> None:
    if isinstance(node, dict):
        for key in list(node):
            value = node[key]
            if value == "":
                del node[key]
                continue
            _strip_empty_strings(value)
    elif isinstance(node, list):
        for item in node:
            _strip_empty_strings(item)
