"""Resolve local CSV payloads to readable file paths."""

from __future__ import annotations

from pathlib import Path

from config_platform_api.config import Settings
from config_platform_api.connectors.base import ConnectorValidationError
from config_platform_api.services.local_csv.path_policy import resolve_allowed_path
from config_platform_api.storage.staging_store import StagingStore


def resolve_csv_path(
    validated: dict[str, object],
    *,
    settings: Settings,
    staging_store: StagingStore,
    connection_ref: str | None = None,
) -> Path:
    location_kind = str(validated.get("location_kind", "local_path"))
    if location_kind == "local_path":
        file_path = str(validated.get("file_path", ""))
        return resolve_allowed_path(file_path, settings.resolved_file_roots())

    if location_kind == "platform_staging":
        staging_file_id = str(validated.get("staging_file_id", ""))
        if not connection_ref:
            raise ConnectorValidationError(
                "Connection ref is required to resolve platform staging files."
            )
        staged_path = staging_store.staged_file_path(connection_ref, staging_file_id)
        if not staged_path.is_file():
            raise ConnectorValidationError(
                f"Staged file '{staging_file_id}' was not found. Upload the CSV before testing."
            )
        return staged_path

    raise ConnectorValidationError(f"Unsupported location_kind: {location_kind}")
