"""Connector factory registry (§7.2.1)."""

from config_platform_api.connectors.azure_sql_database_connector import AzureSqlDatabaseConnector
from config_platform_api.connectors.base import BaseConnector, ConnectorValidationError
from config_platform_api.connectors.csv_s3_bucket_connector import CsvS3BucketConnector
from config_platform_api.connectors.local_csv_connector import LocalCsvConnector
from config_platform_api.connectors.mssql_onprem_connector import MssqlOnPremConnector
from config_platform_api.connectors.mysql_connector import MysqlConnector
from config_platform_api.connectors.postgresql_connector import PostgresqlConnector
from config_platform_api.models.connectors import ConnectorMetadata


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: dict[str, BaseConnector] = {}

    def register(self, connector: BaseConnector) -> None:
        self._connectors[connector.connector_id] = connector

    def get(self, connector_id: str) -> BaseConnector:
        connector = self._connectors.get(connector_id)
        if connector is None:
            raise ConnectorValidationError(f"Unknown connector_id '{connector_id}'.")
        return connector

    def list_metadata(self) -> list[ConnectorMetadata]:
        return [connector.metadata() for connector in self._connectors.values()]


def build_default_registry() -> ConnectorRegistry:
    registry = ConnectorRegistry()
    for connector in (
        LocalCsvConnector(),
        MssqlOnPremConnector(),
        AzureSqlDatabaseConnector(),
        MysqlConnector(),
        PostgresqlConnector(),
        CsvS3BucketConnector(),
    ):
        registry.register(connector)
    return registry


connector_registry = build_default_registry()
