"""Shared fingerprint for test/save verification."""

from config_platform_api.connectors.base import ConnectorValidationError
from config_platform_api.connectors.registry import connector_registry
from config_platform_api.models.connections import ConnectionSaveRequest, ConnectionTestRequest
from config_platform_api.services.connection_builder import ConnectionValidationError, validate_connection_payload


def fingerprint_for_test(request: ConnectionTestRequest) -> str:
    connector = connector_registry.get(request.connector_id)
    try:
        return connector.fingerprint(request.connector_payload)
    except ConnectorValidationError as exc:
        raise ConnectionValidationError(str(exc)) from exc


def fingerprint_for_save(request: ConnectionSaveRequest) -> str:
    validate_connection_payload(request)
    connector = connector_registry.get(request.connector_id)
    return connector.fingerprint(request.connector_payload)
