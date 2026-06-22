"""Shared helpers for bootstrap SQL generation."""

from migration_engine.compilers.bootstrap.connection_string_parser import (
    parse_database_connection_string,
)
from migration_engine.compilers.bootstrap.context import SourceBootstrapContext
from migration_engine.models.connection import DatabaseConnection


def federated_schema_name(connection_ref: str) -> str:
    return f"fed_{connection_ref}"


def federated_table_name(source: SourceBootstrapContext) -> str:
    if source.table_name:
        return source.table_name
    if source.file_name:
        return sanitize_identifier(source.file_name)
    raise ValueError(f"Source alias '{source.alias}' has no table or file name.")


def sanitize_identifier(value: str) -> str:
    base = value.rsplit(".", maxsplit=1)[-1]
    return "".join(character if character.isalnum() else "_" for character in base)


def render_connection_variables(alias: str, connection: DatabaseConnection) -> list[str]:
    params = parse_database_connection_string(connection.connection_string)
    return [
        f"SET @{alias}_host = '{params.host}';",
        f"SET @{alias}_port = {params.port};",
        f"SET @{alias}_database = '{params.database}';",
        f"SET @{alias}_username = '{params.username}';",
        f"SET @{alias}_password = '{params.password}';",
    ]


def render_create_temp_table_as_select(
    bootstrap_table: str,
    federated_schema: str,
    remote_object: str,
) -> str:
    return (
        f"DROP TEMPORARY TABLE IF EXISTS {bootstrap_table};\n"
        f"CREATE TEMPORARY TABLE {bootstrap_table} AS\n"
        f"SELECT *\n"
        f"FROM `{federated_schema}`.`{remote_object}`;"
    )
