"""On-premises Microsoft SQL Server connector adapter."""

from typing import Any

from pydantic import ValidationError
from sqlalchemy.engine import Engine

from config_platform_api.connectors.base import BaseConnector, ConnectorTestResult, ConnectorValidationError
from config_platform_api.connectors.mssql_odbc import build_mssql_odbc_connect, create_mssql_engine
from config_platform_api.connectors.payloads import MssqlOnPremPayload, sql_fields_from_dict
from config_platform_api.connectors.sql_helpers import (
    build_sql_connection_string,
    dispose_sql_engine,
    sanitize_connection_error,
    verify_sql_engine,
)
from config_platform_api.logging_setup import get_logger
from config_platform_api.models.connectors import AuthMethodSchema
from config_platform_api.models.enums import ConnectionType

logger = get_logger(__name__)

P12_AUTH_METHODS = frozenset({"sql_login", "windows_integrated", "windows_login"})


class MssqlOnPremConnector(BaseConnector):
    connector_id = "mssql_onprem"
    label = "SQL Server (on-premises)"
    description = "On-premises Microsoft SQL Server instance."
    category = "database"
    export_type = ConnectionType.MSSQL.value

    def auth_methods(self) -> list[AuthMethodSchema]:
        return [
            AuthMethodSchema(id="sql_login", label="SQL Server authentication", delivery_phase="P1.2"),
            AuthMethodSchema(id="windows_integrated", label="Windows integrated security", delivery_phase="P1.2"),
            AuthMethodSchema(id="windows_login", label="Windows authentication (explicit)", delivery_phase="P1.2"),
            AuthMethodSchema(id="ntlm", label="NTLM (domain user)", delivery_phase="P1.4"),
        ]

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return MssqlOnPremPayload.model_validate(payload).model_dump()
        except ValidationError as exc:
            raise ConnectorValidationError(str(exc)) from exc

    def _fingerprint_body(self, validated: dict[str, Any]) -> dict[str, Any]:
        return validated

    def test_connect(self, payload: dict[str, Any]) -> ConnectorTestResult:
        validated = self.validate(payload)
        if validated["auth_method"] not in P12_AUTH_METHODS:
            return ConnectorTestResult(
                False,
                f"Authentication '{validated['auth_method']}' is available in P1.4.",
            )
        engine: Engine | None = None
        try:
            engine = self._create_engine_from_validated(validated, connect_timeout=5)
            verify_sql_engine(engine)
            summary = f"{validated['host']}:{validated['port']}/{validated['database']}"
            return ConnectorTestResult(True, f"Connected successfully to {summary}.")
        except ConnectorValidationError as exc:
            return ConnectorTestResult(False, str(exc))
        except Exception as exc:
            logger.warning(
                "mssql_onprem_connector_test_failed",
                host=validated.get("host"),
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
            "driver_options": {
                "encrypt": validated["encrypt"],
                "trust_server_certificate": validated["trust_server_certificate"],
            },
        }
        if validated["auth_method"] == "sql_login":
            fields = sql_fields_from_dict(validated)
            exported["connection_string"] = build_sql_connection_string(ConnectionType.MSSQL, fields)
        elif validated["auth_method"] == "windows_integrated":
            exported["connection_string"] = (
                f"sqlserver://{validated['host']}:{validated['port']}/{validated['database']}"
            )
        else:
            exported["connection_string"] = (
                f"sqlserver://{validated['domain']}\\\\{validated['username']}@"
                f"{validated['host']}:{validated['port']}/{validated['database']}"
            )
        if secret_ref is not None:
            exported["secret_ref"] = secret_ref
        return exported

    def create_engine(self, payload: dict[str, Any]) -> Engine:
        validated = self.validate(payload)
        if validated["auth_method"] not in P12_AUTH_METHODS:
            raise ConnectorValidationError(
                f"Introspection for '{validated['auth_method']}' is available in a later phase."
            )
        return self._create_engine_from_validated(validated)

    def build_summary(self, payload: dict[str, Any]) -> str:
        validated = self.validate(payload)
        return f"{validated['host']}:{validated['port']}/{validated['database']}"

    def _create_engine_from_validated(
        self,
        validated: dict[str, Any],
        *,
        connect_timeout: int = 10,
    ) -> Engine:
        odbc_connect = build_mssql_odbc_connect(
            server=validated["host"],
            port=validated["port"],
            database=validated["database"],
            auth_method=validated["auth_method"],
            username=validated.get("username", ""),
            password=validated.get("password", ""),
            domain=validated.get("domain", ""),
            encrypt=validated.get("encrypt", True),
            trust_server_certificate=validated.get("trust_server_certificate", False),
        )
        return create_mssql_engine(odbc_connect, connect_timeout=connect_timeout)
