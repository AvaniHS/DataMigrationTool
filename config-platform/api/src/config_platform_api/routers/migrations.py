from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from config_platform_api.dependencies import get_connection_store, get_migration_store, get_staging_store
from config_platform_api.models.migrations import (
    CreateMigrationRequest,
    MigrationListItem,
    MigrationRecord,
    ReorderBlueprintsRequest,
    UpdateMigrationRequest,
)
from config_platform_api.models.validation import ValidationReportResponse
from config_platform_api.services.migration_export import MigrationExportError, assemble_migration_export
from config_platform_api.services.validation_client import (
    ValidationServiceError,
    to_validation_report_response,
    validate_migration_export,
)
from config_platform_api.services.staging_cleanup import (
    cleanup_staging_for_connection_refs,
    connection_refs_in_migration,
)
from config_platform_api.storage.connection_store import ConnectionStore
from config_platform_api.storage.migration_store import (
    BlueprintNotFoundError,
    MigrationAlreadyExistsError,
    MigrationNotFoundError,
    MigrationStore,
)
from config_platform_api.storage.staging_store import StagingStore

router = APIRouter(prefix="/migrations", tags=["migrations"])


@router.get("", response_model=list[MigrationListItem])
def list_migrations(store: MigrationStore = Depends(get_migration_store)) -> list[MigrationListItem]:
    return store.list_items()


@router.post("", response_model=MigrationRecord, status_code=status.HTTP_201_CREATED)
def create_migration(
    request: CreateMigrationRequest,
    store: MigrationStore = Depends(get_migration_store),
) -> MigrationRecord:
    try:
        return store.create(request)
    except MigrationAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{migration_id}", response_model=MigrationRecord)
def get_migration(
    migration_id: str,
    store: MigrationStore = Depends(get_migration_store),
) -> MigrationRecord:
    try:
        return store.get(migration_id)
    except MigrationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{migration_id}/export", response_model=None)
def export_migration(
    migration_id: str,
    download: bool = Query(default=False, description="Set true to return Content-Disposition attachment."),
    migration_store: MigrationStore = Depends(get_migration_store),
    connection_store: ConnectionStore = Depends(get_connection_store),
) -> JSONResponse | dict[str, object]:
    try:
        migration = migration_store.get(migration_id)
        payload = assemble_migration_export(migration, connection_store)
    except MigrationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MigrationExportError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    if download:
        report = validate_migration_export(payload)
        if not report.get("is_valid"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Migration failed validation. Resolve validation issues before downloading JSON.",
            )
        return JSONResponse(
            content=payload,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{migration_id}.json"',
            },
        )
    return payload


@router.post("/{migration_id}/validate", response_model=ValidationReportResponse)
def validate_migration(
    migration_id: str,
    migration_store: MigrationStore = Depends(get_migration_store),
    connection_store: ConnectionStore = Depends(get_connection_store),
) -> ValidationReportResponse:
    try:
        migration = migration_store.get(migration_id)
        export_payload = assemble_migration_export(migration, connection_store)
        report = validate_migration_export(export_payload)
    except MigrationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MigrationExportError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ValidationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return ValidationReportResponse.model_validate(to_validation_report_response(report))


@router.put("/{migration_id}", response_model=MigrationRecord)
def update_migration(
    migration_id: str,
    request: UpdateMigrationRequest,
    store: MigrationStore = Depends(get_migration_store),
) -> MigrationRecord:
    try:
        return store.update(migration_id, request)
    except MigrationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.delete("/{migration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_migration(
    migration_id: str,
    store: MigrationStore = Depends(get_migration_store),
    connection_store: ConnectionStore = Depends(get_connection_store),
    staging_store: StagingStore = Depends(get_staging_store),
) -> None:
    try:
        migration = store.get(migration_id)
        connection_refs = connection_refs_in_migration(migration)
        store.delete(migration_id)
        cleanup_staging_for_connection_refs(connection_refs, connection_store, staging_store)
    except MigrationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{migration_id}/blueprints", response_model=MigrationRecord)
def add_blueprint(
    migration_id: str,
    store: MigrationStore = Depends(get_migration_store),
) -> MigrationRecord:
    try:
        return store.add_blueprint(migration_id)
    except MigrationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{migration_id}/blueprints/{sequence_order}", response_model=MigrationRecord)
def delete_blueprint(
    migration_id: str,
    sequence_order: int,
    store: MigrationStore = Depends(get_migration_store),
) -> MigrationRecord:
    try:
        return store.delete_blueprint(migration_id, sequence_order)
    except MigrationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BlueprintNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/{migration_id}/blueprints/{sequence_order}/duplicate",
    response_model=MigrationRecord,
)
def duplicate_blueprint(
    migration_id: str,
    sequence_order: int,
    store: MigrationStore = Depends(get_migration_store),
) -> MigrationRecord:
    try:
        return store.duplicate_blueprint(migration_id, sequence_order)
    except MigrationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BlueprintNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{migration_id}/blueprints/reorder", response_model=MigrationRecord)
def reorder_blueprints(
    migration_id: str,
    request: ReorderBlueprintsRequest,
    store: MigrationStore = Depends(get_migration_store),
) -> MigrationRecord:
    try:
        return store.reorder_blueprints(migration_id, request.sequence_orders)
    except MigrationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
