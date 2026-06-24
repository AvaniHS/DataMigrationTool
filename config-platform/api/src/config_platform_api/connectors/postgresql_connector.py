"""PostgreSQL connector adapter."""

from typing import Any

from pydantic import ValidationError
from sqlalchemy.engine import Engine

from config_platform_api.connectors.base import BaseConnector, ConnectorTestResult, ConnectorValidationError
from config_platform_api.connectors.payloads import PostgresqlConnectorPayload, sql_fields_from_dict
from config_platform_api.connectors.sql_helpers import (
    build_sql_connection_string,
    create_sql_engine,
    dispose_sql_engine,
    sanitize_connection_error,
    verify_sql_engine,
)
from config_platform_api.logging_setup import get_logger
from config_platform_api.models.connectors import AuthMethodSchema
from config_platform_api.models.enums import ConnectionType

logger = get_logger(__name__)


class PostgresqlConnector(BaseConnector):
    connector_id = "postgresql"
    label = "PostgreSQL"
    description = "PostgreSQL (on-prem, RDS, Azure Database for PostgreSQL)."
    category = "database"
    export_type = ConnectionType.POSTGRESQL.value

    def auth_methods(self) -> list[AuthMethodSchema]:
        return [AuthMethodSchema(id="password", label="Password", delivery_phase="P1.2")]

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return PostgresqlConnectorPayload.model_validate(payload).model_dump()
        except ValidationError as exc:
            raise ConnectorValidationError(str(exc)) from exc

    def _fingerprint_body(self, validated: dict[str, Any]) -> dict[str, Any]:
        return validated

    def test_connect(self, payload: dict[str, Any]) -> ConnectorTestResult:
        validated = self.validate(payload)
        if validated["auth_method"] != "password":
            return ConnectorTestResult(False, "This authentication method is available in P1.2.")
        engine: Engine | None = None
        try:
            fields = sql_fields_from_dict(validated)
            engine = create_sql_engine(ConnectionType.POSTGRESQL, fields, connect_timeout=5)
            verify_sql_engine(engine)
            summary = f"{validated['host']}:{validated['port']}/{validated['database']}"
            return ConnectorTestResult(True, f"Connected successfully to {summary}.")
        except Exception as exc:
            logger.warning(
                "postgresql_connector_test_failed",
                host=validated.get("host"),
                database=validated.get("database"),
                error=str(exc),
                exc_info=True,
            )
            return ConnectorTestResult(False, sanitize_connection_error(str(exc)))
        finally:
            dispose_sql_engine(engine)

    def build_export(self, payload: dict[str, Any], *, secret_ref: str | None = None) -> dict[str, Any]:
        validated = self.validate(payload)
        fields = sql_fields_from_dict(validated)
        exported: dict[str, Any] = {
            "type": self.export_type,
            "auth_method": validated["auth_method"],
            "connection_string": build_sql_connection_string(ConnectionType.POSTGRESQL, fields),
            "driver_options": {"sslmode": validated["sslmode"]},
        }
        if secret_ref is not None:
            exported["secret_ref"] = secret_ref
        return exported

    def create_engine(self, payload: dict[str, Any]) -> Engine:
        validated = self.validate(payload)
        return create_sql_engine(ConnectionType.POSTGRESQL, sql_fields_from_dict(validated))

    def build_summary(self, payload: dict[str, Any]) -> str:
        validated = self.validate(payload)
        return f"{validated['host']}:{validated['port']}/{validated['database']}"
