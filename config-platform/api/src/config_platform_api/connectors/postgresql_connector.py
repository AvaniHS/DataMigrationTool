"""PostgreSQL connector adapter."""

from typing import Any

from pydantic import ValidationError
from sqlalchemy.engine import Engine

from config_platform_api.connectors.aws_export import build_aws_export_block
from config_platform_api.connectors.aws_rds_iam import generate_rds_auth_token
from config_platform_api.connectors.azure_entra import (
    acquire_azure_oss_rdbms_token_managed_identity,
    acquire_azure_oss_rdbms_token_password,
    acquire_azure_oss_rdbms_token_service_principal,
    build_entra_export_block,
)
from config_platform_api.connectors.base import BaseConnector, ConnectorTestResult, ConnectorValidationError
from config_platform_api.connectors.payloads import (
    ENTRA_MANAGED_IDENTITY,
    ENTRA_PASSWORD,
    ENTRA_SERVICE_PRINCIPAL,
    PASSWORD_SSL_CLIENT_CERT,
    POSTGRESQL_RDS_IAM,
    PostgresqlConnectorPayload,
    sql_fields_from_dict,
)
from config_platform_api.connectors.sql_helpers import (
    build_sql_connection_string,
    create_postgresql_engine,
    create_postgresql_engine_with_rds_token,
    create_postgresql_engine_with_token,
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
        return [
            AuthMethodSchema(id="password", label="Password", delivery_phase="P1.2"),
            AuthMethodSchema(
                id=PASSWORD_SSL_CLIENT_CERT,
                label="Password + client certificate",
                delivery_phase="P1.4",
            ),
            AuthMethodSchema(
                id=ENTRA_PASSWORD,
                label="Microsoft Entra (user/password)",
                delivery_phase="P1.3",
            ),
            AuthMethodSchema(
                id=ENTRA_SERVICE_PRINCIPAL,
                label="Microsoft Entra (service principal)",
                delivery_phase="P1.3",
            ),
            AuthMethodSchema(
                id=ENTRA_MANAGED_IDENTITY,
                label="Managed identity",
                delivery_phase="P1.3",
            ),
            AuthMethodSchema(
                id=POSTGRESQL_RDS_IAM,
                label="AWS RDS IAM",
                delivery_phase="P1.6",
            ),
        ]

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return PostgresqlConnectorPayload.model_validate(payload).model_dump()
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
                "postgresql_connector_test_failed",
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
        sslmode = validated.get("sslmode", "prefer")
        if auth_method == "password":
            fields = sql_fields_from_dict(validated)
            connection_string = build_sql_connection_string(ConnectionType.POSTGRESQL, fields)
        elif auth_method == PASSWORD_SSL_CLIENT_CERT:
            fields = sql_fields_from_dict(validated)
            connection_string = build_sql_connection_string(ConnectionType.POSTGRESQL, fields)
            sslmode = "verify-full"
        elif auth_method == POSTGRESQL_RDS_IAM:
            connection_string = (
                f"postgresql://{validated['username']}@{validated['host']}:"
                f"{validated['port']}/{validated['database']}"
            )
            sslmode = "require"
        else:
            connection_string = (
                f"postgresql://{validated['entra_user']}@{validated['host']}:"
                f"{validated['port']}/{validated['database']}"
            )
            sslmode = "require"
        driver_options: dict[str, object] = {"sslmode": sslmode}
        if auth_method == PASSWORD_SSL_CLIENT_CERT:
            driver_options.update(
                {
                    "sslrootcert": validated.get("sslrootcert", ""),
                    "sslcert": validated.get("sslcert", ""),
                    "sslkey": validated.get("sslkey", ""),
                }
            )
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
            return create_postgresql_engine(
                sql_fields_from_dict(validated),
                sslmode=validated.get("sslmode", "prefer"),
                connect_timeout=connect_timeout,
            )
        if auth_method == PASSWORD_SSL_CLIENT_CERT:
            return create_postgresql_engine(
                sql_fields_from_dict(validated),
                sslmode="verify-full",
                sslrootcert=validated.get("sslrootcert", ""),
                sslcert=validated.get("sslcert", ""),
                sslkey=validated.get("sslkey", ""),
                connect_timeout=connect_timeout,
            )
        if auth_method == POSTGRESQL_RDS_IAM:
            token = generate_rds_auth_token(
                host=validated["host"],
                port=validated["port"],
                username=validated["username"],
                region=validated["aws_region"],
            )
            return create_postgresql_engine_with_rds_token(
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
        elif auth_method == ENTRA_PASSWORD:
            token = acquire_azure_oss_rdbms_token_password(
                validated["tenant_id"],
                validated["client_id"],
                validated["entra_user"],
                validated["entra_password"],
            )
        elif auth_method == ENTRA_MANAGED_IDENTITY:
            token = acquire_azure_oss_rdbms_token_managed_identity(
                validated.get("managed_identity_client_id", ""),
            )
        else:
            raise ConnectorValidationError(f"Unsupported auth method: {auth_method}")

        return create_postgresql_engine_with_token(
            host=validated["host"],
            port=validated["port"],
            database=validated["database"],
            entra_user=validated["entra_user"],
            access_token=token,
            sslmode="require",
            connect_timeout=connect_timeout,
        )
