from fastapi import APIRouter, HTTPException, status

from config_platform_api.connectors.base import ConnectorValidationError
from config_platform_api.connectors.registry import connector_registry
from config_platform_api.models.connectors import ConnectorMetadata, ConnectorSchemaResponse

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.get("", response_model=list[ConnectorMetadata])
def list_connectors() -> list[ConnectorMetadata]:
    return connector_registry.list_metadata()


@router.get("/{connector_id}/schema", response_model=ConnectorSchemaResponse)
def get_connector_schema(connector_id: str) -> ConnectorSchemaResponse:
    try:
        connector = connector_registry.get(connector_id)
    except ConnectorValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    metadata = connector.metadata()
    return ConnectorSchemaResponse(
        connector_id=metadata.connector_id,
        export_type=metadata.export_type,
        category=metadata.category,
        auth_methods=metadata.auth_methods,
        payload_hint=connector.payload_schema_hint(),
    )
