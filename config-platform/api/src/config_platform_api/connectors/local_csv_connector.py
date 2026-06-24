"""Local / staged CSV connector adapter (stub until P1.5)."""

from typing import Any

from pydantic import ValidationError

from config_platform_api.connectors.base import BaseConnector, ConnectorTestResult, ConnectorValidationError
from config_platform_api.connectors.payloads import LocalCsvConnectorPayload
from config_platform_api.models.connectors import AuthMethodSchema
from config_platform_api.models.enums import ConnectionType


class LocalCsvConnector(BaseConnector):
    connector_id = "local_csv"
    label = "Local / staged CSV"
    description = "CSV file via server path or platform upload staging."
    category = "file"
    export_type = ConnectionType.LOCAL_CSV.value

    def auth_methods(self) -> list[AuthMethodSchema]:
        return [
            AuthMethodSchema(id="local_path", label="Local / server path", delivery_phase="P1.5"),
            AuthMethodSchema(id="platform_staging", label="Platform upload", delivery_phase="P1.5"),
        ]

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return LocalCsvConnectorPayload.model_validate(payload).model_dump()
        except ValidationError as exc:
            raise ConnectorValidationError(str(exc)) from exc

    def _fingerprint_body(self, validated: dict[str, Any]) -> dict[str, Any]:
        return validated

    def test_connect(self, payload: dict[str, Any]) -> ConnectorTestResult:
        validated = self.validate(payload)
        return ConnectorTestResult(
            False,
            f"Local CSV '{validated['location_kind']}' verification ships in P1.5.",
        )

    def build_export(self, payload: dict[str, Any], *, secret_ref: str | None = None) -> dict[str, Any]:
        validated = self.validate(payload)
        exported: dict[str, Any] = {
            "type": self.export_type,
            "location_kind": validated["location_kind"],
            "parse_options": validated["parse_options"],
        }
        if validated["location_kind"] == "local_path" and validated["file_path"]:
            exported["file_path"] = validated["file_path"]
        if validated["location_kind"] == "platform_staging" and validated["staging_file_id"]:
            exported["staging_file_id"] = validated["staging_file_id"]
        if secret_ref is not None:
            exported["secret_ref"] = secret_ref
        return exported

    def build_summary(self, payload: dict[str, Any]) -> str:
        validated = self.validate(payload)
        if validated["location_kind"] == "platform_staging":
            return validated["staging_file_id"] or "platform_staging"
        return validated["file_path"] or "local_path"
