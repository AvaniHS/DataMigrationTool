"""MySQL connector adapter."""

from typing import Any

from pydantic import ValidationError
from sqlalchemy.engine import Engine

from config_platform_api.connectors.aws_export import build_aws_export_block
from config_platform_api.connectors.aws_rds_iam import generate_rds_auth_token
from config_platform_api.connectors.azure_entra import (
    acquire_azure_oss_rdbms_token_managed_identity,
    acquire_azure_oss_rdbms_token_service_principal,
    build_entra_export_block,
)
from config_platform_api.connectors.base import BaseConnector, ConnectorTestResult, ConnectorValidationError
from config_platform_api.connectors.payloads import (
    ENTRA_MANAGED_IDENTITY,
    ENTRA_SERVICE_PRINCIPAL,
    MYSQL_RDS_IAM,
    PASSWORD_SSL,
    MysqlConnectorPayload,
    sql_fields_from_dict,
)
from config_platform_api.connectors.sql_helpers import (
    build_sql_connection_string,
    create_mysql_engine,
    create_mysql_engine_with_rds_token,
    create_mysql_engine_with_token,
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
        return [
            AuthMethodSchema(id="password", label="Username & password", delivery_phase="P1.2"),
            AuthMethodSchema(
                id=PASSWORD_SSL,
                label="Username & password (full SSL)",
                delivery_phase="P1.4",
            ),
            AuthMethodSchema(
                id=ENTRA_SERVICE_PRINCIPAL,
                label="Azure Entra (service principal)",
                delivery_phase="P1.3",
            ),
            AuthMethodSchema(
                id=ENTRA_MANAGED_IDENTITY,
                label="Azure Entra (managed identity)",
                delivery_phase="P1.3",
            ),
            AuthMethodSchema(
                id=MYSQL_RDS_IAM,
                label="AWS RDS IAM",
                delivery_phase="P1.6",
            ),
        ]

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
            engine = self._create_engine_from_validated(validated, connect_timeout=5)
            verify_sql_engine(engine)
            summary = f"{validated['host']}:{validated['port']}/{validated['database']}"
            return ConnectorTestResult(True, f"Connected successfully to {summary}.")
        except ConnectorValidationError as exc:
            return ConnectorTestResult(False, str(exc))
        except Exception as exc:
            logger.warning(
                "mysql_connector_test_failed",
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
        auth_method = validated["auth_method"]
        if auth_method == "password":
            fields = sql_fields_from_dict(validated)
            connection_string = build_sql_connection_string(ConnectionType.MYSQL, fields)
            driver_options: dict[str, object] = {"ssl_enabled": validated.get("ssl_enabled", False)}
        elif auth_method == PASSWORD_SSL:
            fields = sql_fields_from_dict(validated)
            connection_string = build_sql_connection_string(ConnectionType.MYSQL, fields)
            driver_options = {
                "ssl_mode": validated.get("ssl_mode", "PREFERRED"),
            }
            if validated.get("ssl_ca_path"):
                driver_options["ssl_ca_path"] = validated["ssl_ca_path"]
        elif auth_method == MYSQL_RDS_IAM:
            connection_string = (
                f"mysql://{validated['username']}@{validated['host']}:{validated['port']}/"
                f"{validated['database']}"
            )
            driver_options = {"ssl_mode": "REQUIRED"}
        else:
            connection_string = (
                f"mysql://{validated['entra_user']}@{validated['host']}:{validated['port']}/"
                f"{validated['database']}"
            )
            driver_options = {"ssl_enabled": True}
        exported: dict[str, Any] = {
            "type": self.export_type,
            "auth_method": auth_method,
            "connection_string": connection_string,
            "driver_options": driver_options,
        }
        entra = build_entra_export_block(validated)
        if entra:
            exported["entra"] = entra
        aws = build_aws_export_block(validated)
        if aws:
            exported["aws"] = aws
        if secret_ref is not None:
            exported["secret_ref"] = secret_ref
        return exported

    def create_engine(self, payload: dict[str, Any]) -> Engine:
        validated = self.validate(payload)
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
        auth_method = validated["auth_method"]
        if auth_method == "password":
            fields = sql_fields_from_dict(validated)
            return create_mysql_engine(
                fields,
                ssl_enabled=validated.get("ssl_enabled", False),
                connect_timeout=connect_timeout,
            )
        if auth_method == PASSWORD_SSL:
            fields = sql_fields_from_dict(validated)
            return create_mysql_engine(
                fields,
                ssl_mode=validated.get("ssl_mode", "PREFERRED"),
                ssl_ca_path=validated.get("ssl_ca_path", ""),
                connect_timeout=connect_timeout,
            )
        if auth_method == MYSQL_RDS_IAM:
            token = generate_rds_auth_token(
                host=validated["host"],
                port=validated["port"],
                username=validated["username"],
                region=validated["aws_region"],
            )
            return create_mysql_engine_with_rds_token(
                host=validated["host"],
                port=validated["port"],
                database=validated["database"],
                username=validated["username"],
                access_token=token,
                connect_timeout=connect_timeout,
            )

        if auth_method == ENTRA_SERVICE_PRINCIPAL:
            token = acquire_azure_oss_rdbms_token_service_principal(
                validated["tenant_id"],
                validated["client_id"],
                validated["client_secret"],
            )
        elif auth_method == ENTRA_MANAGED_IDENTITY:
            token = acquire_azure_oss_rdbms_token_managed_identity(
                validated.get("managed_identity_client_id", ""),
            )
        else:
            raise ConnectorValidationError(f"Unsupported auth method: {auth_method}")

        return create_mysql_engine_with_token(
            host=validated["host"],
            port=validated["port"],
            database=validated["database"],
            entra_user=validated["entra_user"],
            access_token=token,
            connect_timeout=connect_timeout,
        )
