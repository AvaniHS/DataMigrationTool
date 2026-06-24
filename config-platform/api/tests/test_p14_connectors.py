"""Tests for P1.4 SSL/TLS and advanced S3 auth."""

import pytest

from config_platform_api.connectors.base import ConnectorValidationError
from config_platform_api.connectors.payloads import PASSWORD_SSL, PASSWORD_SSL_CLIENT_CERT
from config_platform_api.connectors.registry import connector_registry


def test_mysql_password_ssl_requires_username() -> None:
    connector = connector_registry.get("mysql")
    with pytest.raises(ConnectorValidationError, match="username"):
        connector.validate(
            {
                "auth_method": PASSWORD_SSL,
                "host": "db.local",
                "port": 3306,
                "database": "app",
                "password": "pass",
                "ssl_mode": "REQUIRED",
            }
        )


def test_mysql_password_ssl_export_driver_options() -> None:
    connector = connector_registry.get("mysql")
    exported = connector.build_export(
        {
            "auth_method": PASSWORD_SSL,
            "host": "db.local",
            "port": 3306,
            "database": "app",
            "username": "user",
            "password": "pass",
            "ssl_mode": "VERIFY_CA",
            "ssl_ca_path": "/etc/ssl/ca.pem",
        }
    )
    assert exported["driver_options"] == {
        "ssl_mode": "VERIFY_CA",
        "ssl_ca_path": "/etc/ssl/ca.pem",
    }


def test_postgresql_client_cert_requires_paths() -> None:
    connector = connector_registry.get("postgresql")
    with pytest.raises(ConnectorValidationError, match="sslrootcert"):
        connector.validate(
            {
                "auth_method": PASSWORD_SSL_CLIENT_CERT,
                "host": "pg.local",
                "port": 5432,
                "database": "app",
                "username": "user",
                "password": "pass",
                "sslcert": "/client.crt",
                "sslkey": "/client.key",
            }
        )


def test_postgresql_client_cert_export() -> None:
    connector = connector_registry.get("postgresql")
    exported = connector.build_export(
        {
            "auth_method": PASSWORD_SSL_CLIENT_CERT,
            "host": "pg.local",
            "port": 5432,
            "database": "app",
            "username": "user",
            "password": "pass",
            "sslrootcert": "/ca.pem",
            "sslcert": "/client.crt",
            "sslkey": "/client.key",
        }
    )
    assert exported["driver_options"]["sslmode"] == "verify-full"
    assert exported["driver_options"]["sslcert"] == "/client.crt"


def test_s3_session_token_requires_token() -> None:
    connector = connector_registry.get("csv_s3_bucket")
    with pytest.raises(ConnectorValidationError, match="session_token"):
        connector.validate(
            {
                "auth_method": "session_token",
                "s3_bucket_uri": "s3://bucket/prefix/",
                "aws_region": "us-east-1",
                "access_key_id": "AKIA",
                "secret_access_key": "secret",
            }
        )


def test_s3_assume_role_export() -> None:
    connector = connector_registry.get("csv_s3_bucket")
    exported = connector.build_export(
        {
            "auth_method": "assume_role",
            "s3_bucket_uri": "s3://bucket/prefix/",
            "aws_region": "us-east-1",
            "role_arn": "arn:aws:iam::123456789012:role/read",
            "external_id": "ext",
        }
    )
    assert exported["auth_method"] == "assume_role"
    assert exported["role_arn"] == "arn:aws:iam::123456789012:role/read"
    assert exported["external_id"] == "ext"
    assert "access_key_id" not in exported


def test_mssql_ntlm_requires_domain() -> None:
    connector = connector_registry.get("mssql_onprem")
    with pytest.raises(ConnectorValidationError, match="domain"):
        connector.validate(
            {
                "auth_method": "ntlm",
                "host": "sql01",
                "port": 1433,
                "database": "app",
                "username": "svc",
                "password": "secret",
            }
        )
