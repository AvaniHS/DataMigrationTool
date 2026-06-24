"""Create SQLAlchemy engines from stored connection records."""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL, make_url

from config_platform_api.models.connections import ConnectionRecord, DatabaseConnectionFields
from config_platform_api.models.enums import ConnectionType
from config_platform_api.services.connection_builder import build_database_connection_string


def create_database_engine(
    connection_type: ConnectionType,
    fields: DatabaseConnectionFields,
    *,
    connect_timeout: int = 10,
) -> Engine:
    connection_string = build_database_connection_string(connection_type, fields)
    url = to_sqlalchemy_url(connection_type, connection_string)
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": connect_timeout})


def create_engine_for_record(record: ConnectionRecord, *, connect_timeout: int = 10) -> Engine:
    if record.type == ConnectionType.CSV_S3_BUCKET:
        raise ValueError("S3 connections do not use SQLAlchemy engines.")
    if record.database is None:
        raise ValueError("Database fields are required.")
    return create_database_engine(record.type, record.database, connect_timeout=connect_timeout)


def to_sqlalchemy_url(connection_type: ConnectionType, connection_string: str) -> URL:
    url = make_url(connection_string)
    if connection_type == ConnectionType.MYSQL:
        return url.set(drivername="mysql+pymysql")
    if connection_type == ConnectionType.POSTGRESQL:
        return url.set(drivername="postgresql+psycopg2")
    if connection_type == ConnectionType.MSSQL:
        return _mssql_sqlalchemy_url(url)
    raise ValueError(f"Unsupported connection type: {connection_type}")


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


def verify_database_connection(engine: Engine) -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def dispose_engine(engine: Engine | None) -> None:
    if engine is not None:
        engine.dispose()
