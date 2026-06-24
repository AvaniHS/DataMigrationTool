"""Tests for P1.2 connector payload validation."""

import pytest

from config_platform_api.connectors.base import ConnectorValidationError
from config_platform_api.connectors.registry import connector_registry


def test_s3_access_key_requires_credentials() -> None:
    connector = connector_registry.get("csv_s3_bucket")
    with pytest.raises(ConnectorValidationError, match="access_key_id"):
        connector.validate(
            {
                "auth_method": "access_key",
                "s3_bucket_uri": "s3://bucket/prefix/",
                "aws_region": "us-east-1",
            }
        )


def test_mssql_windows_login_requires_domain() -> None:
    connector = connector_registry.get("mssql_onprem")
    with pytest.raises(ConnectorValidationError, match="domain"):
        connector.validate(
            {
                "auth_method": "windows_login",
                "host": "sql01",
                "port": 1433,
                "database": "app",
                "username": "svc",
                "password": "secret",
            }
        )


def test_mysql_export_includes_driver_options() -> None:
    connector = connector_registry.get("mysql")
    exported = connector.build_export(
        {
            "auth_method": "password",
            "host": "db.local",
            "port": 3306,
            "database": "app",
            "username": "user",
            "password": "pass",
            "ssl_enabled": True,
        }
    )
    assert exported["auth_method"] == "password"
    assert exported["driver_options"] == {"ssl_enabled": True}
