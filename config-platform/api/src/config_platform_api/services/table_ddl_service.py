"""Create target tables via structure copy and audit templates."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from config_platform_api.exceptions import DdlError
from config_platform_api.models.enums import ConnectionType
from config_platform_api.models.introspection import ColumnNode
from config_platform_api.models.table_ddl import TableColumnSpec


def copy_table_structure(
    engine: Engine,
    connection_type: ConnectionType,
    *,
    source_schema: str,
    source_table: str,
    destination_schema: str,
    destination_table: str,
) -> str:
    if table_exists(engine, connection_type, destination_schema, destination_table):
        raise DdlError(
            f"Table {destination_schema}.{destination_table} already exists on the target connection.",
        )
    if not table_exists(engine, connection_type, source_schema, source_table):
        raise DdlError(f"Source table {source_schema}.{source_table} was not found.")

    ddl = _build_copy_structure_ddl(
        connection_type,
        source_schema=source_schema,
        source_table=source_table,
        destination_schema=destination_schema,
        destination_table=destination_table,
    )
    with engine.begin() as connection:
        connection.execute(text(ddl))
    return ddl


def create_audit_table(
    engine: Engine,
    connection_type: ConnectionType,
    *,
    destination_schema: str,
    destination_table: str,
    migration_id: str,
    blueprint_sequence: int,
    target_schema: str,
    target_table: str,
    primary_key_columns: list[str],
    target_columns: list[TableColumnSpec],
) -> str:
    if table_exists(engine, connection_type, destination_schema, destination_table):
        raise DdlError(
            f"Table {destination_schema}.{destination_table} already exists on the target connection.",
        )

    ddl = _build_audit_table_ddl(
        connection_type,
        destination_schema=destination_schema,
        destination_table=destination_table,
        migration_id=migration_id,
        blueprint_sequence=blueprint_sequence,
        target_schema=target_schema,
        target_table=target_table,
        primary_key_columns=primary_key_columns,
        target_columns=target_columns,
    )
    with engine.begin() as connection:
        connection.execute(text(ddl))
    return ddl


def table_exists(
    engine: Engine,
    connection_type: ConnectionType,
    schema: str,
    table: str,
) -> bool:
    query = _table_exists_query(connection_type)
    with engine.connect() as connection:
        row = connection.execute(text(query), {"schema": schema, "table": table}).first()
    return bool(row)


def _table_exists_query(connection_type: ConnectionType) -> str:
    if connection_type in (ConnectionType.MYSQL, ConnectionType.POSTGRESQL):
        return """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = :schema AND table_name = :table
            LIMIT 1
        """
    if connection_type == ConnectionType.MSSQL:
        return """
            SELECT 1
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table
        """
    raise DdlError(f"Unsupported connection type: {connection_type}")


def _build_copy_structure_ddl(
    connection_type: ConnectionType,
    *,
    source_schema: str,
    source_table: str,
    destination_schema: str,
    destination_table: str,
) -> str:
    source = _qualify(connection_type, source_schema, source_table)
    destination = _qualify(connection_type, destination_schema, destination_table)

    if connection_type == ConnectionType.MYSQL:
        return f"CREATE TABLE {destination} LIKE {source}"
    if connection_type == ConnectionType.POSTGRESQL:
        return (
            f"CREATE TABLE {destination} "
            f"(LIKE {source} INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES)"
        )
    if connection_type == ConnectionType.MSSQL:
        return (
            f"SELECT * INTO {destination} FROM {source} WHERE 1 = 0"
        )
    raise DdlError(f"Unsupported connection type: {connection_type}")


def _build_audit_table_ddl(
    connection_type: ConnectionType,
    *,
    destination_schema: str,
    destination_table: str,
    migration_id: str,
    blueprint_sequence: int,
    target_schema: str,
    target_table: str,
    primary_key_columns: list[str],
    target_columns: list[TableColumnSpec],
) -> str:
    destination = _qualify(connection_type, destination_schema, destination_table)
    column_defs: list[str] = []

    for column in target_columns:
        sql_type = _map_column_type(connection_type, column.data_type)
        nullable = "NULL" if column.is_nullable else "NOT NULL"
        column_defs.append(f"{_quote_ident(connection_type, column.name)} {sql_type} {nullable}")

    column_defs.append(
        f"{_quote_ident(connection_type, 'rejected_at')} {_timestamp_type(connection_type)} NULL",
    )
    column_defs.append(
        f"{_quote_ident(connection_type, 'logged_at')} {_timestamp_type(connection_type)} "
        f"NOT NULL DEFAULT {_timestamp_default(connection_type)}",
    )
    column_defs.append(
        f"{_quote_ident(connection_type, 'migration_id')} {_varchar_type(connection_type, 128)} NOT NULL "
        f"DEFAULT {_string_literal(connection_type, migration_id)}",
    )
    column_defs.append(
        f"{_quote_ident(connection_type, 'blueprint_sequence')} INT NOT NULL "
        f"DEFAULT {blueprint_sequence}",
    )
    column_defs.append(
        f"{_quote_ident(connection_type, 'target_schema')} {_varchar_type(connection_type, 128)} NOT NULL "
        f"DEFAULT {_string_literal(connection_type, target_schema)}",
    )
    column_defs.append(
        f"{_quote_ident(connection_type, 'target_table')} {_varchar_type(connection_type, 128)} NOT NULL "
        f"DEFAULT {_string_literal(connection_type, target_table)}",
    )

    for pk_column in primary_key_columns:
        if any(column.name == pk_column for column in target_columns):
            continue
        column_defs.append(
            f"{_quote_ident(connection_type, pk_column)} {_varchar_type(connection_type, 512)} NULL",
        )

    column_defs.append(
        f"{_quote_ident(connection_type, 'source_snapshot')} {_text_type(connection_type)} NULL",
    )
    column_defs.append(
        f"{_quote_ident(connection_type, 'reject_reason')} {_varchar_type(connection_type, 64)} NULL",
    )
    column_defs.append(
        f"{_quote_ident(connection_type, 'raw_row')} {_text_type(connection_type)} NULL",
    )

    body = ",\n  ".join(column_defs)
    return f"CREATE TABLE {destination} (\n  {body}\n)"


def column_specs_from_nodes(columns: list[ColumnNode]) -> list[TableColumnSpec]:
    return [
        TableColumnSpec(name=column.name, data_type=column.data_type, is_nullable=column.is_nullable)
        for column in columns
    ]


def _qualify(connection_type: ConnectionType, schema: str, table: str) -> str:
    return f"{_quote_ident(connection_type, schema)}.{_quote_ident(connection_type, table)}"


def _quote_ident(connection_type: ConnectionType, identifier: str) -> str:
    if connection_type == ConnectionType.MYSQL:
        return f"`{identifier.replace('`', '``')}`"
    if connection_type == ConnectionType.POSTGRESQL:
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'
    if connection_type == ConnectionType.MSSQL:
        return f"[{identifier.replace(']', ']]')}]"
    raise DdlError(f"Unsupported connection type: {connection_type}")


def _map_column_type(connection_type: ConnectionType, data_type: str) -> str:
    normalized = data_type.strip().lower()
    if connection_type == ConnectionType.POSTGRESQL:
        if normalized in {"int", "integer", "bigint", "smallint"}:
            return normalized.upper()
        if normalized in {"varchar", "character varying", "text"}:
            return "TEXT" if normalized == "text" else "VARCHAR(512)"
        if "timestamp" in normalized or normalized == "datetime":
            return "TIMESTAMP"
        if normalized in {"decimal", "numeric", "double", "float", "real"}:
            return "DOUBLE PRECISION"
        return "TEXT"
    if connection_type == ConnectionType.MSSQL:
        if normalized in {"int", "integer", "bigint", "smallint"}:
            return "BIGINT"
        if "timestamp" in normalized or normalized == "datetime":
            return "DATETIME2"
        if normalized in {"decimal", "numeric", "double", "float", "real"}:
            return "FLOAT"
        return "NVARCHAR(MAX)"
    if normalized in {"int", "integer", "bigint", "smallint", "tinyint", "mediumint"}:
        return "BIGINT"
    if normalized in {"decimal", "numeric", "double", "float"}:
        return "DOUBLE"
    if "timestamp" in normalized or normalized == "datetime":
        return "DATETIME"
    if normalized in {"varchar", "char", "text", "longtext", "mediumtext"}:
        return "TEXT"
    return "TEXT"


def _timestamp_type(connection_type: ConnectionType) -> str:
    if connection_type == ConnectionType.POSTGRESQL:
        return "TIMESTAMP"
    if connection_type == ConnectionType.MSSQL:
        return "DATETIME2"
    return "DATETIME"


def _timestamp_default(connection_type: ConnectionType) -> str:
    if connection_type == ConnectionType.POSTGRESQL:
        return "CURRENT_TIMESTAMP"
    if connection_type == ConnectionType.MSSQL:
        return "SYSUTCDATETIME()"
    return "CURRENT_TIMESTAMP"


def _varchar_type(connection_type: ConnectionType, length: int) -> str:
    if connection_type == ConnectionType.POSTGRESQL:
        return f"VARCHAR({length})"
    if connection_type == ConnectionType.MSSQL:
        return f"NVARCHAR({length})"
    return f"VARCHAR({length})"


def _text_type(connection_type: ConnectionType) -> str:
    if connection_type == ConnectionType.MSSQL:
        return "NVARCHAR(MAX)"
    return "TEXT"


def _string_literal(connection_type: ConnectionType, value: str) -> str:
    escaped = value.replace("'", "''")
    if connection_type == ConnectionType.MSSQL:
        return f"N'{escaped}'"
    return f"'{escaped}'"
