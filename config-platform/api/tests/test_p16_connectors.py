"""Tests for P1.6 AWS RDS IAM auth."""

import pytest

from config_platform_api.connectors.base import ConnectorValidationError
from config_platform_api.connectors.payloads import MYSQL_RDS_IAM, POSTGRESQL_RDS_IAM
from config_platform_api.connectors.registry import connector_registry


def test_mysql_rds_iam_requires_aws_region() -> None:
    connector = connector_registry.get("mysql")
    with pytest.raises(ConnectorValidationError, match="aws_region"):
        connector.validate(
            {
                "auth_method": MYSQL_RDS_IAM,
                "host": "mydb.abc123.us-east-1.rds.amazonaws.com",
                "port": 3306,
                "database": "app",
                "username": "iam_user",
            }
        )


def test_mysql_rds_iam_export_omits_password() -> None:
    connector = connector_registry.get("mysql")
    exported = connector.build_export(
        {
            "auth_method": MYSQL_RDS_IAM,
            "host": "mydb.abc123.us-east-1.rds.amazonaws.com",
            "port": 3306,
            "database": "app",
            "username": "iam_user",
            "aws_region": "us-east-1",
        }
    )
    assert exported["auth_method"] == MYSQL_RDS_IAM
    assert "iam_user@" in exported["connection_string"]
    assert "password" not in exported["connection_string"]
    assert exported["aws"] == {"region": "us-east-1"}
    assert exported["driver_options"] == {"ssl_mode": "REQUIRED"}


def test_postgresql_rds_iam_export() -> None:
    connector = connector_registry.get("postgresql")
    exported = connector.build_export(
        {
            "auth_method": POSTGRESQL_RDS_IAM,
            "host": "mydb.abc123.us-east-1.rds.amazonaws.com",
            "port": 5432,
            "database": "app",
            "username": "iam_user",
            "aws_region": "us-east-1",
        }
    )
    assert exported["auth_method"] == POSTGRESQL_RDS_IAM
    assert exported["aws"] == {"region": "us-east-1"}
    assert exported["driver_options"] == {"sslmode": "require"}
