"""Bootstrap strategy for PostgreSQL sources."""

from migration_engine.compilers.bootstrap._sql_helpers import (
    federated_schema_name,
    federated_table_name,
    render_connection_variables,
    render_create_temp_table_as_select,
)
from migration_engine.compilers.bootstrap.base_bootstrap import ISourceBootstrapStrategy
from migration_engine.compilers.bootstrap.context import SourceBootstrapRequest
from migration_engine.models.connection import DatabaseConnection


class PostgreSqlSourceBootstrapStrategy(ISourceBootstrapStrategy):
    """Bootstrap a PostgreSQL table through a MySQL federated bridge."""

    def build_preamble(self, request: SourceBootstrapRequest) -> str:
        source = request.source
        connection = request.connection
        if not isinstance(connection, DatabaseConnection):
            raise TypeError("PostgreSQL source bootstrap requires a database connection.")

        if not source.schema_name or not source.table_name:
            raise ValueError(f"PostgreSQL source '{source.alias}' requires schema and table_name.")

        federated_schema = federated_schema_name(source.connection_ref)
        remote_table = federated_table_name(source)
        lines = [
            f"-- Bootstrap POSTGRESQL source '{source.alias}' "
            f"({source.connection_ref}.{source.schema_name}.{source.table_name})",
            "-- Requires PostgreSQL federated bridge mapped into MySQL.",
            *render_connection_variables(source.alias, connection),
            render_create_temp_table_as_select(
                source.bootstrap_table,
                federated_schema,
                remote_table,
            ),
        ]
        return "\n".join(lines)
