"""Assemble export-ready connection config from structured fields."""

from urllib.parse import quote_plus

from config_platform_api.models.connections import (
    ConnectionPayload,
    ConnectionRecord,
    DatabaseConnectionFields,
    ExportedDatabaseConnection,
    ExportedS3Connection,
    S3ConnectionFields,
)
from config_platform_api.models.enums import ConnectionType


class ConnectionValidationError(ValueError):
    """Raised when connection payload does not match its declared type."""


def _require_database_fields(payload: ConnectionPayload) -> DatabaseConnectionFields:
    if payload.database is None:
        raise ConnectionValidationError(f"Database fields are required for {payload.type.value}.")
    if payload.s3 is not None:
        raise ConnectionValidationError("S3 fields are not allowed for database connections.")
    return payload.database


def _require_s3_fields(payload: ConnectionPayload) -> S3ConnectionFields:
    if payload.s3 is None:
        raise ConnectionValidationError("S3 fields are required for CSV_S3_BUCKET connections.")
    if payload.database is not None:
        raise ConnectionValidationError("Database fields are not allowed for S3 connections.")
    return payload.s3


def build_database_connection_string(
    connection_type: ConnectionType,
    fields: DatabaseConnectionFields,
) -> str:
    if fields.use_advanced_string and fields.connection_string:
        return fields.connection_string.strip()

    user = quote_plus(fields.username)
    password = quote_plus(fields.password)
    host = fields.host.strip()
    port = fields.port
    database = quote_plus(fields.database)

    if connection_type == ConnectionType.MYSQL:
        return f"mysql://{user}:{password}@{host}:{port}/{database}"
    if connection_type == ConnectionType.POSTGRESQL:
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    if connection_type == ConnectionType.MSSQL:
        return f"sqlserver://{user}:{password}@{host}:{port}/{database}"

    raise ConnectionValidationError(f"Unsupported database connection type: {connection_type}")


def build_connection_summary(payload: ConnectionPayload) -> str:
    if payload.type == ConnectionType.CSV_S3_BUCKET:
        s3 = _require_s3_fields(payload)
        return s3.s3_bucket_uri

    database = _require_database_fields(payload)
    return f"{database.host}:{database.port}/{database.database}"


def to_export_dict(payload: ConnectionPayload) -> dict[str, str]:
    if payload.type == ConnectionType.CSV_S3_BUCKET:
        s3 = _require_s3_fields(payload)
        exported = ExportedS3Connection(
            type=ConnectionType.CSV_S3_BUCKET,
            s3_bucket_uri=s3.s3_bucket_uri,
            aws_region=s3.aws_region,
        )
        return exported.model_dump()

    database = _require_database_fields(payload)
    exported = ExportedDatabaseConnection(
        type=payload.type,
        connection_string=build_database_connection_string(payload.type, database),
    )
    return exported.model_dump()


def validate_payload_shape(payload: ConnectionPayload) -> None:
    if payload.type == ConnectionType.CSV_S3_BUCKET:
        _require_s3_fields(payload)
        return
    _require_database_fields(payload)


def record_to_export_dict(record: ConnectionRecord) -> dict[str, str]:
    validate_payload_shape(record)
    return to_export_dict(record)
