"""Orchestrate verified connection saves."""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from pydantic import ValidationError

from config_platform_api.logging_setup import get_logger
from config_platform_api.models.connections import ConnectionRecord, ConnectionSaveRequest
from config_platform_api.services.connection_builder import ConnectionValidationError
from config_platform_api.services.connection_fingerprint import fingerprint_for_save
from config_platform_api.services.verification_store import VerificationStore
from config_platform_api.storage.connection_store import (
    ConnectionAlreadyExistsError,
    ConnectionNotFoundError,
    ConnectionStore,
)

logger = get_logger(__name__)


def save_verified_connection(
    request: ConnectionSaveRequest,
    store: ConnectionStore,
    verification_store: VerificationStore,
    *,
    is_create: bool,
) -> ConnectionRecord:
    try:
        fingerprint = fingerprint_for_save(request)
    except (ConnectionValidationError, ValidationError) as exc:
        logger.warning("connection_save_validation_failed", ref=request.ref, detail=str(exc))
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    if not verification_store.consume(request.verification_token, fingerprint):
        logger.warning("connection_save_missing_verification", ref=request.ref)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connection must be tested successfully before save.",
        )

    tested_at = datetime.now(UTC)
    try:
        if is_create:
            return store.create(request, tested_at=tested_at)
        return store.update(request.ref, request, tested_at=tested_at)
    except ConnectionAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ConnectionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
