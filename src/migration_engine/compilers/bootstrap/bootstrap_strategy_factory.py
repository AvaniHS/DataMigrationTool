"""Factory for source bootstrap strategies."""

from migration_engine.compilers.bootstrap.base_bootstrap import ISourceBootstrapStrategy
from migration_engine.compilers.bootstrap.mssql_source_bootstrap import MsSqlSourceBootstrapStrategy
from migration_engine.compilers.bootstrap.mysql_source_bootstrap import MySqlSourceBootstrapStrategy
from migration_engine.compilers.bootstrap.postgresql_source_bootstrap import (
    PostgreSqlSourceBootstrapStrategy,
)
from migration_engine.compilers.bootstrap.s3_csv_source_bootstrap import S3CsvSourceBootstrapStrategy
from migration_engine.models.enums import ConnectionType


class BootstrapStrategyFactory:
    """Creates bootstrap strategies by source connection type."""

    _registry: dict[str, type[ISourceBootstrapStrategy]] = {
        ConnectionType.MYSQL.value: MySqlSourceBootstrapStrategy,
        ConnectionType.MSSQL.value: MsSqlSourceBootstrapStrategy,
        ConnectionType.POSTGRESQL.value: PostgreSqlSourceBootstrapStrategy,
        ConnectionType.CSV_S3_BUCKET.value: S3CsvSourceBootstrapStrategy,
    }

    @classmethod
    def create(cls, connection_type: str) -> ISourceBootstrapStrategy:
        strategy_cls = cls._registry.get(connection_type.upper())
        if strategy_cls is None:
            supported = ", ".join(sorted(cls._registry))
            raise ValueError(
                f"Unsupported bootstrap connection type '{connection_type}'. "
                f"Supported: {supported}"
            )
        return strategy_cls()
