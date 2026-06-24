import pytest

from config_platform_api.connectors.legacy import migrate_legacy_connection_record
from config_platform_api.connectors.mysql_connector import MysqlConnector
from config_platform_api.connectors.registry import ConnectorRegistry, build_default_registry
from config_platform_api.connectors.sql_helpers import build_sql_connection_string
from config_platform_api.connectors.payloads import SqlPasswordFields
from config_platform_api.models.enums import ConnectionType


def test_default_registry_registers_six_connectors() -> None:
    registry = build_default_registry()
    connector_ids = {item.connector_id for item in registry.list_metadata()}
    assert connector_ids == {
        "local_csv",
        "mssql_onprem",
        "azure_sql_database",
        "mysql",
        "postgresql",
        "csv_s3_bucket",
    }


def test_mysql_connector_build_export() -> None:
    connector = MysqlConnector()
    exported = connector.build_export(
        {
            "auth_method": "password",
            "host": "client-crm-ip",
            "port": 3306,
            "database": "crm_db",
            "username": "read_user",
            "password": "pass",
        },
    )
    assert exported["type"] == "MYSQL"
    assert exported["connection_string"] == "mysql://read_user:pass@client-crm-ip:3306/crm_db"


def test_build_mysql_connection_string() -> None:
    fields = SqlPasswordFields(
        host="client-crm-ip",
        port=3306,
        database="crm_db",
        username="read_user",
        password="pass",
    )
    assert (
        build_sql_connection_string(ConnectionType.MYSQL, fields)
        == "mysql://read_user:pass@client-crm-ip:3306/crm_db"
    )


def test_migrate_legacy_mysql_record() -> None:
    migrated = migrate_legacy_connection_record(
        {
            "ref": "client_crm_mysql",
            "type": "MYSQL",
            "secret_ref": None,
            "database": {
                "host": "client-crm-ip",
                "port": 3306,
                "database": "crm_db",
                "username": "read_user",
                "password": "pass",
                "use_advanced_string": False,
            },
        },
    )
    assert migrated["connector_id"] == "mysql"
    assert migrated["connector_payload"]["auth_method"] == "password"
    assert migrated["connector_payload"]["host"] == "client-crm-ip"


def test_unknown_connector_raises() -> None:
    registry = ConnectorRegistry()
    with pytest.raises(Exception):
        registry.get("unknown")
