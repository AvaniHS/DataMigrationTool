"""Full local_csv connector adapter (P1.5)."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from config_platform_api.config import Settings, get_settings
from config_platform_api.connectors.base import BaseConnector, ConnectorTestResult, ConnectorValidationError
from config_platform_api.connectors.payloads import LocalCsvConnectorPayload
from config_platform_api.models.connectors import AuthMethodSchema
from config_platform_api.models.enums import ConnectionType
from config_platform_api.services.local_csv.csv_sample import read_csv_column_names
from config_platform_api.services.local_csv.resolver import resolve_csv_path
from config_platform_api.storage.staging_store import StagingStore


class LocalCsvConnector(BaseConnector):
    connector_id = "local_csv"
    label = "Local / staged CSV"
    description = "CSV file via server path or platform upload staging."
    category = "file"
    export_type = ConnectionType.LOCAL_CSV.value

    def auth_methods(self) -> list[AuthMethodSchema]:
        return [
            AuthMethodSchema(id="local_path", label="Local / server path", delivery_phase="P1"),
            AuthMethodSchema(id="platform_staging", label="Platform upload", delivery_phase="P1"),
        ]

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            model = LocalCsvConnectorPayload.model_validate(payload)
            return {
                **model.model_dump(),
                "parse_options": model.parse_options.model_dump(),
            }
        except ValidationError as exc:
            raise ConnectorValidationError(str(exc)) from exc

    def _fingerprint_body(self, validated: dict[str, Any]) -> dict[str, Any]:
        return validated

    def test_connect(self, payload: dict[str, Any], **context: Any) -> ConnectorTestResult:
        validated = self.validate(payload)
        settings: Settings = context.get("settings") or get_settings()
        staging_store: StagingStore = context.get("staging_store") or StagingStore(settings.staging_dir)
        connection_ref: str | None = context.get("connection_ref")

        try:
            path = resolve_csv_path(
                validated,
                settings=settings,
                staging_store=staging_store,
                connection_ref=connection_ref,
            )
            if not path.is_file():
                return ConnectorTestResult(False, "CSV file was not found at the configured path.")
            columns = read_csv_column_names(path, validated["parse_options"])
        except ConnectorValidationError as exc:
            return ConnectorTestResult(False, str(exc))

        preview = ", ".join(columns[:8])
        suffix = "…" if len(columns) > 8 else ""
        return ConnectorTestResult(
            True,
            f"CSV readable. {len(columns)} column(s): {preview}{suffix}",
        )

    def build_export(self, payload: dict[str, Any], *, secret_ref: str | None = None) -> dict[str, Any]:
        validated = self.validate(payload)
        exported: dict[str, Any] = {
            "type": self.export_type,
            "location_kind": validated["location_kind"],
            "parse_options": validated["parse_options"],
        }
        if validated["location_kind"] == "local_path":
            exported["file_path"] = validated["file_path"]
        if validated["location_kind"] == "platform_staging":
            exported["staging_file_id"] = validated["staging_file_id"]
        if secret_ref is not None:
            exported["secret_ref"] = secret_ref
        return exported

    def build_summary(self, payload: dict[str, Any]) -> str:
        validated = self.validate(payload)
        if validated["location_kind"] == "platform_staging":
            return validated["staging_file_id"] or "platform_staging"
        return validated["file_path"] or "local_path"
