"""Shared fingerprint for test/save verification."""

import hashlib
import json

from config_platform_api.models.connections import (
    ConnectionSaveRequest,
    ConnectionTestRequest,
    DatabaseConnectionFields,
    S3ConnectionFields,
)
from config_platform_api.models.enums import ConnectionType
from config_platform_api.services.connection_builder import ConnectionValidationError


def validate_test_request(request: ConnectionTestRequest) -> None:
    if request.type == ConnectionType.CSV_S3_BUCKET:
        if request.s3 is None:
            raise ConnectionValidationError("S3 fields are required for CSV_S3_BUCKET connections.")
        return
    if request.database is None:
        raise ConnectionValidationError(f"Database fields are required for {request.type.value}.")


def connection_body_fingerprint(
    connection_type: ConnectionType,
    database: DatabaseConnectionFields | None,
    s3: S3ConnectionFields | None,
) -> str:
    canonical = {
        "type": connection_type.value,
        "database": database.model_dump(mode="json") if database else None,
        "s3": s3.model_dump(mode="json") if s3 else None,
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def fingerprint_for_test(request: ConnectionTestRequest) -> str:
    validate_test_request(request)
    return connection_body_fingerprint(request.type, request.database, request.s3)


def fingerprint_for_save(request: ConnectionSaveRequest) -> str:
    from config_platform_api.services.connection_builder import validate_payload_shape

    validate_payload_shape(request)
    return connection_body_fingerprint(request.type, request.database, request.s3)
