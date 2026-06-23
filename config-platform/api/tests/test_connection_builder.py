import pytest

from config_platform_api.models.connections import ConnectionPayload, DatabaseConnectionFields
from config_platform_api.models.enums import ConnectionType
from config_platform_api.services.connection_builder import (
    build_database_connection_string,
    to_export_dict,
)


def test_build_mysql_connection_string() -> None:
    fields = DatabaseConnectionFields(
        host="client-crm-ip",
        port=3306,
        database="crm_db",
        username="read_user",
        password="pass",
    )
    assert (
        build_database_connection_string(ConnectionType.MYSQL, fields)
        == "mysql://read_user:pass@client-crm-ip:3306/crm_db"
    )


def test_build_mssql_connection_string() -> None:
    fields = DatabaseConnectionFields(
        host="client-billing-ip",
        port=1433,
        database="finance_db",
        username="read_user",
        password="pass",
    )
    exported = to_export_dict(
        ConnectionPayload(
            ref="client_billing_mssql",
            type=ConnectionType.MSSQL,
            database=fields,
        ),
    )
    assert exported["type"] == "MSSQL"
    assert exported["connection_string"].startswith("sqlserver://read_user:pass@")


def test_export_s3_connection() -> None:
    exported = to_export_dict(
        ConnectionPayload(
            ref="client_archival_s3",
            type=ConnectionType.CSV_S3_BUCKET,
            s3={
                "s3_bucket_uri": "s3://client-migration-dump/historical_archives/",
                "aws_region": "us-west-2",
            },
        ),
    )
    assert exported == {
        "type": "CSV_S3_BUCKET",
        "s3_bucket_uri": "s3://client-migration-dump/historical_archives/",
        "aws_region": "us-west-2",
    }


def test_advanced_connection_string_override() -> None:
    fields = DatabaseConnectionFields(
        host="ignored",
        port=3306,
        database="crm_db",
        username="user",
        password="pass",
        use_advanced_string=True,
        connection_string="mysql://custom:uri@host:3306/crm_db",
    )
    assert (
        build_database_connection_string(ConnectionType.MYSQL, fields)
        == "mysql://custom:uri@host:3306/crm_db"
    )
