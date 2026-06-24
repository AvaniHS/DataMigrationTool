from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from config_platform_api.dependencies import get_connection_store, get_verification_store
from config_platform_api.logging_setup import get_logger
from config_platform_api.models.connections import (
    ConnectionListItem,
    ConnectionRecord,
    ConnectionSaveRequest,
    ConnectionTestRequest,
    ConnectionTestResponse,
)
from config_platform_api.services.connection_fingerprint import fingerprint_for_test
from config_platform_api.services.connection_service import save_verified_connection
from config_platform_api.services.connection_tester import test_connection
from config_platform_api.services.verification_store import VerificationStore
from config_platform_api.storage.connection_store import ConnectionNotFoundError, ConnectionStore

router = APIRouter(prefix="/connections", tags=["connections"])
logger = get_logger(__name__)


@router.get("", response_model=list[ConnectionListItem])
def list_connections(store: ConnectionStore = Depends(get_connection_store)) -> list[ConnectionListItem]:
    return store.list_items()


@router.get("/export")
def export_connections(store: ConnectionStore = Depends(get_connection_store)) -> dict[str, dict[str, object]]:
    return store.export_all()


@router.get("/{ref}", response_model=ConnectionRecord)
def get_connection(
    ref: str,
    store: ConnectionStore = Depends(get_connection_store),
) -> ConnectionRecord:
    try:
        return store.get(ref)
    except ConnectionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/test", response_model=ConnectionTestResponse)
def test_connection_endpoint(
    request: ConnectionTestRequest,
    verification_store: VerificationStore = Depends(get_verification_store),
) -> ConnectionTestResponse:
    from config_platform_api.services.connection_builder import ConnectionValidationError

    try:
        fingerprint = fingerprint_for_test(request)
    except ConnectionValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    result = test_connection(request)
    if not result.success:
        logger.warning(
            "connection_test_failed",
            connector_id=request.connector_id,
            message=result.message,
        )
        return ConnectionTestResponse(success=False, message=result.message)

    token = verification_store.issue(fingerprint)
    logger.info("connection_test_succeeded", connector_id=request.connector_id)
    return ConnectionTestResponse(success=True, message=result.message, verification_token=token)


@router.post("", response_model=ConnectionRecord, status_code=status.HTTP_201_CREATED)
def create_connection(
    request: ConnectionSaveRequest,
    store: ConnectionStore = Depends(get_connection_store),
    verification_store: VerificationStore = Depends(get_verification_store),
) -> ConnectionRecord:
    return save_verified_connection(request, store, verification_store, is_create=True)


@router.put("/{ref}", response_model=ConnectionRecord)
def update_connection(
    ref: str,
    request: ConnectionSaveRequest,
    store: ConnectionStore = Depends(get_connection_store),
    verification_store: VerificationStore = Depends(get_verification_store),
) -> ConnectionRecord:
    if ref != request.ref:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connection ref in path and body must match.",
        )
    return save_verified_connection(request, store, verification_store, is_create=False)


@router.delete("/{ref}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    ref: str,
    store: ConnectionStore = Depends(get_connection_store),
) -> None:
    try:
        store.delete(ref)
    except ConnectionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
