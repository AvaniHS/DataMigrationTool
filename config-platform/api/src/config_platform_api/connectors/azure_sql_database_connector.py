"""Azure SQL Database connector adapter."""

from typing import Any

from pydantic import ValidationError
from sqlalchemy.engine import Engine

from config_platform_api.connectors.base import BaseConnector, ConnectorTestResult, ConnectorValidationError
from config_platform_api.connectors.payloads import AzureSqlDatabasePayload, SqlPasswordFields
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


class AzureSqlDatabaseConnector(BaseConnector):
    connector_id = "azure_sql_database"
    label = "Azure SQL Database"
    description = "Azure SQL Database or Managed Instance (*.database.windows.net)."
    category = "database"
    export_type = ConnectionType.MSSQL.value

    def auth_methods(self) -> list[AuthMethodSchema]:
        return [
            AuthMethodSchema(id="sql_login", label="SQL authentication", delivery_phase="P1.2"),
            AuthMethodSchema(
                id="entra_service_principal",
                label="Microsoft Entra ID (service principal)",
                delivery_phase="P1.2",
            ),
            AuthMethodSchema(id="entra_password", label="Microsoft Entra ID (user/password)", delivery_phase="P1.3"),
            AuthMethodSchema(id="entra_managed_identity", label="Managed identity", delivery_phase="P1.3"),
        ]

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return AzureSqlDatabasePayload.model_validate(payload).model_dump()
        except ValidationError as exc:
            raise ConnectorValidationError(str(exc)) from exc

    def _fingerprint_body(self, validated: dict[str, Any]) -> dict[str, Any]:
        return validated

    def test_connect(self, payload: dict[str, Any]) -> ConnectorTestResult:
        validated = self.validate(payload)
        if validated["auth_method"] != "sql_login":
            return ConnectorTestResult(
                False,
                f"Authentication '{validated['auth_method']}' is available in P1.2 or P1.3.",
            )
        engine: Engine | None = None
        try:
            fields = SqlPasswordFields(
                host=validated["server"],
                port=1433,
                database=validated["database"],
                username=validated["username"],
                password=validated["password"],
                use_advanced_string=validated["use_advanced_string"],
                connection_string=validated["connection_string"],
            )
            engine = create_sql_engine(ConnectionType.MSSQL, fields, connect_timeout=5)
            verify_sql_engine(engine)
            summary = f"{validated['server']}/{validated['database']}"
            return ConnectorTestResult(True, f"Connected successfully to {summary}.")
        except Exception as exc:
            logger.warning(
                "azure_sql_connector_test_failed",
                server=validated.get("server"),
                database=validated.get("database"),
                error=str(exc),
                exc_info=True,
            )
            return ConnectorTestResult(False, sanitize_connection_error(str(exc)))
        finally:
            dispose_sql_engine(engine)

    def build_export(self, payload: dict[str, Any], *, secret_ref: str | None = None) -> dict[str, Any]:
        validated = self.validate(payload)
        fields = SqlPasswordFields(
            host=validated["server"],
            port=1433,
            database=validated["database"],
            username=validated["username"],
            password=validated["password"],
            use_advanced_string=validated["use_advanced_string"],
            connection_string=validated["connection_string"],
        )
        exported: dict[str, Any] = {
            "type": self.export_type,
            "auth_method": validated["auth_method"],
            "connection_string": build_sql_connection_string(ConnectionType.MSSQL, fields),
            "driver_options": {"encrypt": True, "trust_server_certificate": False},
        }
        if secret_ref is not None:
            exported["secret_ref"] = secret_ref
        return exported

    def create_engine(self, payload: dict[str, Any]) -> Engine:
        validated = self.validate(payload)
        if validated["auth_method"] != "sql_login":
            raise ConnectorValidationError("Only sql_login supports introspection in P1.1.")
        fields = SqlPasswordFields(
            host=validated["server"],
            port=1433,
            database=validated["database"],
            username=validated["username"],
            password=validated["password"],
            use_advanced_string=validated["use_advanced_string"],
            connection_string=validated["connection_string"],
        )
        return create_sql_engine(ConnectionType.MSSQL, fields)

    def build_summary(self, payload: dict[str, Any]) -> str:
        validated = self.validate(payload)
        return f"{validated['server']}/{validated['database']}"
