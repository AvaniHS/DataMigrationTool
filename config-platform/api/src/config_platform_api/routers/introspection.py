from fastapi import APIRouter, Depends, HTTPException, status

from config_platform_api.config import Settings, get_settings
from config_platform_api.dependencies import get_connection_store, get_staging_store
from config_platform_api.exceptions import IntrospectionError
from config_platform_api.exceptions import DdlError
from config_platform_api.models.introspection import ColumnNode, SchemaNode, S3FileNode, TableNode
from config_platform_api.models.table_ddl import CopyStructureRequest, CopyStructureResponse
from config_platform_api.services.introspection import introspection_service
from config_platform_api.services.table_ddl import execute_copy_structure
from config_platform_api.storage.connection_store import ConnectionStore
from config_platform_api.storage.staging_store import StagingStore

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


@router.post("/{ref}/tables/copy-structure", response_model=CopyStructureResponse)
def copy_connection_table_structure(
    ref: str,
    request: CopyStructureRequest,
    store: ConnectionStore = Depends(get_connection_store),
    settings: Settings = Depends(get_settings),
) -> CopyStructureResponse:
    try:
        return execute_copy_structure(store, ref, request, settings)
    except IntrospectionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DdlError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/{ref}/files", response_model=list[S3FileNode])
def list_connection_files(
    ref: str,
    store: ConnectionStore = Depends(get_connection_store),
    settings: Settings = Depends(get_settings),
    staging_store: StagingStore = Depends(get_staging_store),
) -> list[S3FileNode]:
    try:
        return introspection_service.list_files(store, ref, settings, staging_store)
    except IntrospectionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{ref}/files/{file_name}/columns", response_model=list[ColumnNode])
def list_connection_file_columns(
    ref: str,
    file_name: str,
    store: ConnectionStore = Depends(get_connection_store),
    settings: Settings = Depends(get_settings),
    staging_store: StagingStore = Depends(get_staging_store),
) -> list[ColumnNode]:
    try:
        return introspection_service.list_file_columns(store, ref, file_name, settings, staging_store)
    except IntrospectionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
