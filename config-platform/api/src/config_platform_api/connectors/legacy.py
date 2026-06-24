"""Migrate P1 flat connection records to connector_id + connector_payload."""

from typing import Any

from config_platform_api.models.enums import ConnectionType


_LEGACY_TYPE_TO_CONNECTOR: dict[str, str] = {
    ConnectionType.MYSQL.value: "mysql",
    ConnectionType.POSTGRESQL.value: "postgresql",
    ConnectionType.MSSQL.value: "mssql_onprem",
    ConnectionType.CSV_S3_BUCKET.value: "csv_s3_bucket",
}


def is_legacy_connection_record(payload: dict[str, Any]) -> bool:
    return "connector_id" not in payload and "type" in payload


def migrate_legacy_connection_record(payload: dict[str, Any]) -> dict[str, Any]:
    if not is_legacy_connection_record(payload):
        return payload

    connection_type = payload["type"]
    connector_id = _LEGACY_TYPE_TO_CONNECTOR.get(connection_type)
    if connector_id is None:
        raise ValueError(f"Unsupported legacy connection type: {connection_type}")

    if connection_type == ConnectionType.CSV_S3_BUCKET.value:
        s3 = payload.get("s3") or {}
        connector_payload = {
            "auth_method": "access_key",
            "s3_bucket_uri": s3.get("s3_bucket_uri", ""),
            "aws_region": s3.get("aws_region", ""),
        }
    elif connection_type == ConnectionType.MYSQL.value:
        database = payload.get("database") or {}
        connector_payload = {"auth_method": "password", **database}
    elif connection_type == ConnectionType.POSTGRESQL.value:
        database = payload.get("database") or {}
        connector_payload = {"auth_method": "password", "sslmode": "prefer", **database}
    else:
        database = payload.get("database") or {}
        connector_payload = {"auth_method": "sql_login", **database}

    migrated = {key: value for key, value in payload.items() if key not in {"type", "database", "s3"}}
    migrated["connector_id"] = connector_id
    migrated["connector_payload"] = connector_payload
    return migrated
