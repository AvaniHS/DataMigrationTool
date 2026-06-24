"""Test connectivity via connector adapters."""

from config_platform_api.config import Settings, get_settings
from config_platform_api.connectors.base import ConnectorTestResult
from config_platform_api.connectors.registry import connector_registry
from config_platform_api.models.connections import ConnectionTestRequest
from config_platform_api.storage.staging_store import StagingStore


def test_connection(
    request: ConnectionTestRequest,
    *,
    settings: Settings | None = None,
    staging_store: StagingStore | None = None,
) -> ConnectorTestResult:
    resolved_settings = settings or get_settings()
    resolved_staging = staging_store or StagingStore(resolved_settings.staging_dir)
    connector = connector_registry.get(request.connector_id)
    validated = connector.validate(request.connector_payload)
    context: dict[str, object] = {}
    if request.connector_id == "local_csv":
        context = {
            "connection_ref": request.connection_ref,
            "settings": resolved_settings,
            "staging_store": resolved_staging,
        }
    return connector.test_connect(validated, **context)
