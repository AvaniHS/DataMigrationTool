"""Tests for P1.3 Entra connector payloads and export."""

import pytest

from config_platform_api.connectors.base import ConnectorValidationError
from config_platform_api.connectors.registry import connector_registry


def test_azure_entra_password_requires_user_fields() -> None:
    connector = connector_registry.get("azure_sql_database")
    with pytest.raises(ConnectorValidationError, match="entra_user"):
        connector.validate(
            {
                "auth_method": "entra_password",
                "server": "myserver.database.windows.net",
                "database": "app",
                "tenant_id": "tenant",
                "client_id": "client",
                "entra_password": "secret",
            }
        )


def test_mysql_entra_export_omits_secrets() -> None:
    connector = connector_registry.get("mysql")
    exported = connector.build_export(
        {
            "auth_method": "entra_service_principal",
            "host": "mydb.mysql.database.azure.com",
            "port": 3306,
            "database": "app",
            "entra_user": "user@contoso.com",
            "tenant_id": "tenant-guid",
            "client_id": "client-guid",
            "client_secret": "top-secret",
        }
    )
    assert exported["auth_method"] == "entra_service_principal"
    assert "top-secret" not in exported["connection_string"]
    assert exported["entra"] == {
        "tenant_id": "tenant-guid",
        "client_id": "client-guid",
        "entra_user": "user@contoso.com",
    }
    assert "client_secret" not in exported


def test_postgresql_entra_managed_identity_export() -> None:
    connector = connector_registry.get("postgresql")
    exported = connector.build_export(
        {
            "auth_method": "entra_managed_identity",
            "host": "mydb.postgres.database.azure.com",
            "port": 5432,
            "database": "app",
            "entra_user": "user@contoso.com",
            "managed_identity_client_id": "mi-guid",
        }
    )
    assert exported["auth_method"] == "entra_managed_identity"
    assert exported["driver_options"] == {"sslmode": "require"}
    assert exported["entra"]["managed_identity_client_id"] == "mi-guid"
