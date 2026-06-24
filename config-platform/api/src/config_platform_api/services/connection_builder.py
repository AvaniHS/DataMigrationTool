"""Assemble export-ready connection config via connector adapters."""

from config_platform_api.connectors.registry import connector_registry
from config_platform_api.models.connections import ConnectionPayload, ConnectionRecord


class ConnectionValidationError(ValueError):
    """Raised when connection payload does not match its connector."""


def validate_connection_payload(payload: ConnectionPayload) -> dict[str, object]:
    connector = connector_registry.get(payload.connector_id)
    return connector.validate(payload.connector_payload)


def build_connection_summary(record: ConnectionPayload) -> str:
    connector = connector_registry.get(record.connector_id)
    validated = connector.validate(record.connector_payload)
    return connector.build_summary(validated)


def record_to_export_dict(record: ConnectionRecord) -> dict[str, object]:
    connector = connector_registry.get(record.connector_id)
    validated = connector.validate(record.connector_payload)
    return connector.build_export(validated, secret_ref=record.secret_ref)
