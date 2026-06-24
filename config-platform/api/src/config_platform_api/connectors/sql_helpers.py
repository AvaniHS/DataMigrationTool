"""Shared SQL connection string and engine helpers for database connectors."""

from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL, make_url

from config_platform_api.connectors.base import ConnectorValidationError
from config_platform_api.connectors.payloads import SqlPasswordFields
from config_platform_api.models.enums import ConnectionType


def build_sql_connection_string(
    export_type: ConnectionType,
    fields: SqlPasswordFields,
) -> str:
    if fields.use_advanced_string and fields.connection_string:
        return fields.connection_string.strip()

    user = quote_plus(fields.username)
    password = quote_plus(fields.password)
    host = fields.host.strip()
    port = fields.port
    database = quote_plus(fields.database)

    if export_type == ConnectionType.MYSQL:
        return f"mysql://{user}:{password}@{host}:{port}/{database}"
    if export_type == ConnectionType.POSTGRESQL:
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    if export_type == ConnectionType.MSSQL:
        return f"sqlserver://{user}:{password}@{host}:{port}/{database}"

    raise ConnectorValidationError(f"Unsupported export type: {export_type}")


def to_sqlalchemy_url(export_type: ConnectionType, connection_string: str) -> URL:
    url = make_url(connection_string)
    if export_type == ConnectionType.MYSQL:
        return url.set(drivername="mysql+pymysql")
    if export_type == ConnectionType.POSTGRESQL:
        return url.set(drivername="postgresql+psycopg2")
    if export_type == ConnectionType.MSSQL:
        return _mssql_sqlalchemy_url(url)
    raise ConnectorValidationError(f"Unsupported export type: {export_type}")


def create_sql_engine(
    export_type: ConnectionType,
    fields: SqlPasswordFields,
    *,
    connect_timeout: int = 10,
) -> Engine:
    connection_string = build_sql_connection_string(export_type, fields)
    url = to_sqlalchemy_url(export_type, connection_string)
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": connect_timeout})


def verify_sql_engine(engine: Engine) -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def dispose_sql_engine(engine: Engine | None) -> None:
    if engine is not None:
        engine.dispose()


def _mssql_sqlalchemy_url(url: URL) -> URL:
    host = url.host or "localhost"
    port = url.port or 1433
    database = (url.database or "").lstrip("/")
    username = url.username or ""
    password = url.password or ""
    odbc_connect = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host},{port};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"TrustServerCertificate=yes;"
    )
    return URL.create("mssql+pyodbc", query={"odbc_connect": odbc_connect})


def sanitize_connection_error(message: str) -> str:
    lowered = message.lower()
    if "password" in lowered or "access denied" in lowered:
        return "Connection failed. Check host, credentials, and network access."
    if len(message) > 240:
        return f"{message[:237]}..."
    return message
