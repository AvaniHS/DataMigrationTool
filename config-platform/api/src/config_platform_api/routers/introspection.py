from fastapi import APIRouter, Depends, HTTPException, status

from config_platform_api.config import Settings, get_settings
from config_platform_api.dependencies import get_connection_store
from config_platform_api.exceptions import IntrospectionError
from config_platform_api.models.introspection import ColumnNode, SchemaNode, S3FileNode, TableNode
from config_platform_api.services.introspection import introspection_service
from config_platform_api.storage.connection_store import ConnectionStore

router = APIRouter(prefix="/connections", tags=["introspection"])


@router.get("/{ref}/schemas", response_model=list[SchemaNode])
def list_connection_schemas(
    ref: str,
    store: ConnectionStore = Depends(get_connection_store),
    settings: Settings = Depends(get_settings),
) -> list[SchemaNode]:
    try:
        return introspection_service.list_schemas(store, ref, settings)
    except IntrospectionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{ref}/schemas/{schema}/tables", response_model=list[TableNode])
def list_connection_tables(
    ref: str,
    schema: str,
    store: ConnectionStore = Depends(get_connection_store),
    settings: Settings = Depends(get_settings),
) -> list[TableNode]:
    try:
        return introspection_service.list_tables(store, ref, schema, settings)
    except IntrospectionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/{ref}/schemas/{schema}/tables/{table}/columns",
    response_model=list[ColumnNode],
)
def list_connection_columns(
    ref: str,
    schema: str,
    table: str,
    store: ConnectionStore = Depends(get_connection_store),
    settings: Settings = Depends(get_settings),
) -> list[ColumnNode]:
    try:
        return introspection_service.list_columns(store, ref, schema, table, settings)
    except IntrospectionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{ref}/files", response_model=list[S3FileNode])
def list_connection_files(
    ref: str,
    store: ConnectionStore = Depends(get_connection_store),
    settings: Settings = Depends(get_settings),
) -> list[S3FileNode]:
    try:
        return introspection_service.list_files(store, ref, settings)
    except IntrospectionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
