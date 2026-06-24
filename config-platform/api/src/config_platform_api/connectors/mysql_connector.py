"""MySQL connector adapter."""

from typing import Any

from pydantic import ValidationError
from sqlalchemy.engine import Engine

from config_platform_api.connectors.base import BaseConnector, ConnectorTestResult, ConnectorValidationError
from config_platform_api.connectors.payloads import MysqlConnectorPayload, sql_fields_from_dict
from config_platform_api.connectors.sql_helpers import (
    build_sql_connection_string,
    create_mysql_engine,
    dispose_sql_engine,
    sanitize_connection_error,
    verify_sql_engine,
)
from config_platform_api.logging_setup import get_logger
from config_platform_api.models.connectors import AuthMethodSchema
from config_platform_api.models.enums import ConnectionType

logger = get_logger(__name__)


class MysqlConnector(BaseConnector):
    connector_id = "mysql"
    label = "MySQL"
    description = "MySQL or MariaDB database (on-prem, VM, RDS, Azure Database for MySQL)."
    category = "database"
    export_type = ConnectionType.MYSQL.value

    def auth_methods(self) -> list[AuthMethodSchema]:
        return [AuthMethodSchema(id="password", label="Username & password", delivery_phase="P1.2")]

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return MysqlConnectorPayload.model_validate(payload).model_dump()
        except ValidationError as exc:
            raise ConnectorValidationError(str(exc)) from exc

    def _fingerprint_body(self, validated: dict[str, Any]) -> dict[str, Any]:
        return validated

    def test_connect(self, payload: dict[str, Any]) -> ConnectorTestResult:
        validated = self.validate(payload)
        engine: Engine | None = None
        try:
            fields = sql_fields_from_dict(validated)
            engine = create_mysql_engine(
                fields,
                ssl_enabled=validated.get("ssl_enabled", False),
                connect_timeout=5,
            )
            verify_sql_engine(engine)
            summary = f"{validated['host']}:{validated['port']}/{validated['database']}"
            return ConnectorTestResult(True, f"Connected successfully to {summary}.")
        except Exception as exc:
            logger.warning(
                "mysql_connector_test_failed",
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
            "connection_string": build_sql_connection_string(ConnectionType.MYSQL, fields),
            "driver_options": {"ssl_enabled": validated.get("ssl_enabled", False)},
        }
        if secret_ref is not None:
            exported["secret_ref"] = secret_ref
        return exported

    def create_engine(self, payload: dict[str, Any]) -> Engine:
        validated = self.validate(payload)
        fields = sql_fields_from_dict(validated)
        return create_mysql_engine(fields, ssl_enabled=validated.get("ssl_enabled", False))

    def build_summary(self, payload: dict[str, Any]) -> str:
        validated = self.validate(payload)
        return f"{validated['host']}:{validated['port']}/{validated['database']}"
