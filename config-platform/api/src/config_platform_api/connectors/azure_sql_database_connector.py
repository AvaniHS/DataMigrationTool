"""Azure SQL Database connector adapter."""

from typing import Any

from pydantic import ValidationError
from sqlalchemy.engine import Engine

from config_platform_api.connectors.azure_entra import (
    acquire_azure_sql_token_managed_identity,
    acquire_azure_sql_token_password,
    acquire_azure_sql_token_service_principal,
    build_entra_export_block,
)
from config_platform_api.connectors.base import BaseConnector, ConnectorTestResult, ConnectorValidationError
from config_platform_api.connectors.mssql_odbc import build_mssql_odbc_connect, create_mssql_engine
from config_platform_api.connectors.payloads import (
    ENTRA_MANAGED_IDENTITY,
    ENTRA_PASSWORD,
    ENTRA_SERVICE_PRINCIPAL,
    AzureSqlDatabasePayload,
    SqlPasswordFields,
)
from config_platform_api.connectors.sql_helpers import (
    build_sql_connection_string,
    create_mssql_engine_with_access_token,
    dispose_sql_engine,
    sanitize_connection_error,
    verify_sql_engine,
)
from config_platform_api.logging_setup import get_logger
from config_platform_api.models.connectors import AuthMethodSchema
from config_platform_api.models.enums import ConnectionType

logger = get_logger(__name__)

SUPPORTED_AUTH_METHODS = frozenset(
    {"sql_login", ENTRA_SERVICE_PRINCIPAL, ENTRA_PASSWORD, ENTRA_MANAGED_IDENTITY}
)


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
                id=ENTRA_SERVICE_PRINCIPAL,
                label="Microsoft Entra ID (service principal)",
                delivery_phase="P1.2",
            ),
            AuthMethodSchema(
                id=ENTRA_PASSWORD,
                label="Microsoft Entra ID (user/password)",
                delivery_phase="P1.3",
            ),
            AuthMethodSchema(
                id=ENTRA_MANAGED_IDENTITY,
                label="Managed identity",
                delivery_phase="P1.3",
            ),
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
        engine: Engine | None = None
        try:
            engine = self._create_engine_from_validated(validated, connect_timeout=5)
            verify_sql_engine(engine)
            summary = f"{validated['server']}/{validated['database']}"
            return ConnectorTestResult(True, f"Connected successfully to {summary}.")
        except ConnectorValidationError as exc:
            return ConnectorTestResult(False, str(exc))
        except Exception as exc:
            logger.warning(
                "azure_sql_connector_test_failed",
                server=validated.get("server"),
                database=validated.get("database"),
                auth_method=validated.get("auth_method"),
                error=str(exc),
                exc_info=True,
            )
            return ConnectorTestResult(False, sanitize_connection_error(str(exc)))
        finally:
            dispose_sql_engine(engine)

    def build_export(self, payload: dict[str, Any], *, secret_ref: str | None = None) -> dict[str, Any]:
        validated = self.validate(payload)
        exported: dict[str, Any] = {
            "type": self.export_type,
            "auth_method": validated["auth_method"],
            "connection_string": f"sqlserver://{validated['server']}:1433/{validated['database']}",
            "driver_options": {
                "encrypt": validated["encrypt"],
                "trust_server_certificate": validated["trust_server_certificate"],
            },
        }
        if validated["auth_method"] == "sql_login":
            fields = SqlPasswordFields(
                host=validated["server"],
                port=1433,
                database=validated["database"],
                username=validated["username"],
                password=validated["password"],
                use_advanced_string=validated["use_advanced_string"],
                connection_string=validated["connection_string"],
            )
            exported["connection_string"] = build_sql_connection_string(ConnectionType.MSSQL, fields)
        else:
            entra = build_entra_export_block(validated)
            if entra:
                exported["entra"] = entra
        if secret_ref is not None:
            exported["secret_ref"] = secret_ref
        return exported

    def create_engine(self, payload: dict[str, Any]) -> Engine:
        validated = self.validate(payload)
        return self._create_engine_from_validated(validated)

    def build_summary(self, payload: dict[str, Any]) -> str:
        validated = self.validate(payload)
        return f"{validated['server']}/{validated['database']}"

    def _create_engine_from_validated(
        self,
        validated: dict[str, Any],
        *,
        connect_timeout: int = 10,
    ) -> Engine:
        auth_method = validated["auth_method"]
        encrypt = validated.get("encrypt", True)
        trust = validated.get("trust_server_certificate", False)

        if auth_method == "sql_login":
            odbc_connect = build_mssql_odbc_connect(
                server=validated["server"],
                port=1433,
                database=validated["database"],
                auth_method="sql_login",
                username=validated["username"],
                password=validated["password"],
                encrypt=encrypt,
                trust_server_certificate=trust,
            )
            return create_mssql_engine(odbc_connect, connect_timeout=connect_timeout)

        if auth_method == ENTRA_SERVICE_PRINCIPAL:
            access_token = acquire_azure_sql_token_service_principal(
                validated["tenant_id"],
                validated["client_id"],
                validated["client_secret"],
            )
        elif auth_method == ENTRA_PASSWORD:
            access_token = acquire_azure_sql_token_password(
                validated["tenant_id"],
                validated["client_id"],
                validated["entra_user"],
                validated["entra_password"],
            )
        elif auth_method == ENTRA_MANAGED_IDENTITY:
            access_token = acquire_azure_sql_token_managed_identity(
                validated.get("managed_identity_client_id", ""),
            )
        else:
            raise ConnectorValidationError(f"Unsupported auth method: {auth_method}")

        return create_mssql_engine_with_access_token(
            server=validated["server"],
            database=validated["database"],
            access_token=access_token,
            encrypt=encrypt,
            trust_server_certificate=trust,
            connect_timeout=connect_timeout,
        )
