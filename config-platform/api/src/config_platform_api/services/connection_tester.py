"""Test connectivity via connector adapters."""

from config_platform_api.connectors.base import ConnectorTestResult
from config_platform_api.connectors.registry import connector_registry
from config_platform_api.models.connections import ConnectionTestRequest


def test_connection(request: ConnectionTestRequest) -> ConnectorTestResult:
    connector = connector_registry.get(request.connector_id)
    validated = connector.validate(request.connector_payload)
    return connector.test_connect(validated)
