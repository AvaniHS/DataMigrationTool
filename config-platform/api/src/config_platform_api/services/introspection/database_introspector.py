"""Database schema introspection via parameterized metadata queries."""

from sqlalchemy import text
from sqlalchemy.engine import Engine

from config_platform_api.models.enums import ConnectionType
from config_platform_api.models.introspection import ColumnNode, SchemaNode, TableNode


def list_schemas(engine: Engine, connection_type: ConnectionType) -> list[SchemaNode]:
    query = _schemas_query(connection_type)
    with engine.connect() as connection:
        rows = connection.execute(text(query)).mappings().all()
    return [SchemaNode(name=row["name"]) for row in rows]


def list_tables(engine: Engine, connection_type: ConnectionType, schema: str) -> list[TableNode]:
    query = _tables_query(connection_type)
    with engine.connect() as connection:
        rows = connection.execute(text(query), {"schema": schema}).mappings().all()
    return [TableNode(name=row["name"], schema_name=schema) for row in rows]


def list_columns(
    engine: Engine,
    connection_type: ConnectionType,
    schema: str,
    table: str,
) -> list[ColumnNode]:
    query = _columns_query(connection_type)
    with engine.connect() as connection:
        rows = (
            connection.execute(text(query), {"schema": schema, "table": table})
            .mappings()
            .all()
        )
    return [
        ColumnNode(
            name=row["name"],
            data_type=row["data_type"],
            is_nullable=row["is_nullable"] in ("YES", True),
        )
        for row in rows
    ]


def _schemas_query(connection_type: ConnectionType) -> str:
    if connection_type == ConnectionType.MYSQL:
        return """
            SELECT SCHEMA_NAME AS name
            FROM information_schema.SCHEMATA
            WHERE SCHEMA_NAME NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
            ORDER BY SCHEMA_NAME
        """
    if connection_type == ConnectionType.POSTGRESQL:
        return """
            SELECT schema_name AS name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schema_name
        """
    if connection_type == ConnectionType.MSSQL:
        return """
            SELECT name
            FROM sys.schemas
            ORDER BY name
        """
    raise ValueError(f"Unsupported connection type: {connection_type}")


def _tables_query(connection_type: ConnectionType) -> str:
    if connection_type in (ConnectionType.MYSQL, ConnectionType.POSTGRESQL):
        return """
            SELECT table_name AS name
            FROM information_schema.tables
            WHERE table_schema = :schema AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
    if connection_type == ConnectionType.MSSQL:
        return """
            SELECT TABLE_NAME AS name
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = :schema AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """
    raise ValueError(f"Unsupported connection type: {connection_type}")


def _columns_query(connection_type: ConnectionType) -> str:
    if connection_type in (ConnectionType.MYSQL, ConnectionType.POSTGRESQL):
        return """
            SELECT column_name AS name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = :schema AND table_name = :table
            ORDER BY ordinal_position
        """
    if connection_type == ConnectionType.MSSQL:
        return """
            SELECT COLUMN_NAME AS name, DATA_TYPE AS data_type, IS_NULLABLE AS is_nullable
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = :table
            ORDER BY ORDINAL_POSITION
        """
    raise ValueError(f"Unsupported connection type: {connection_type}")
