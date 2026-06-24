"""Shared SQL connection string and engine helpers for database connectors."""

from __future__ import annotations

import ssl
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL, make_url

from config_platform_api.connectors.base import ConnectorValidationError
from config_platform_api.connectors.mssql_odbc import strip_sqlalchemy_error_suffix
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
        raise ConnectorValidationError("Use create_mssql_engine via mssql_odbc for MSSQL connections.")
    raise ConnectorValidationError(f"Unsupported export type: {export_type}")


def _mysql_ssl_connect_arg(ssl_mode: str, ssl_ca_path: str = "") -> dict[str, object]:
    mode = ssl_mode.upper()
    if mode == "DISABLED":
        return {}
    if mode == "PREFERRED":
        return {"ssl": {"ssl": True}}

    context = ssl.create_default_context()
    if ssl_ca_path:
        context.load_verify_locations(ssl_ca_path)
    if mode == "REQUIRED":
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    elif mode == "VERIFY_CA":
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED
    elif mode == "VERIFY_IDENTITY":
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = True
    return {"ssl": context}


def create_mysql_engine(
    fields: SqlPasswordFields,
    *,
    ssl_enabled: bool = False,
    ssl_mode: str | None = None,
    ssl_ca_path: str = "",
    connect_timeout: int = 10,
) -> Engine:
    connection_string = build_sql_connection_string(ConnectionType.MYSQL, fields)
    url = to_sqlalchemy_url(ConnectionType.MYSQL, connection_string)
    connect_args: dict[str, object] = {"connect_timeout": connect_timeout}
    if ssl_mode:
        connect_args.update(_mysql_ssl_connect_arg(ssl_mode, ssl_ca_path))
    elif ssl_enabled:
        connect_args["ssl"] = {"ssl": True}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


def create_postgresql_engine(
    fields: SqlPasswordFields,
    *,
    sslmode: str = "prefer",
    sslrootcert: str = "",
    sslcert: str = "",
    sslkey: str = "",
    connect_timeout: int = 10,
) -> Engine:
    connection_string = build_sql_connection_string(ConnectionType.POSTGRESQL, fields)
    url = to_sqlalchemy_url(ConnectionType.POSTGRESQL, connection_string)
    query: dict[str, str] = {"sslmode": sslmode}
    if sslrootcert:
        query["sslrootcert"] = sslrootcert
    if sslcert:
        query["sslcert"] = sslcert
    if sslkey:
        query["sslkey"] = sslkey
    url = url.update_query_dict(**query)
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": connect_timeout})


def create_mysql_engine_with_rds_token(
    *,
    host: str,
    port: int,
    database: str,
    username: str,
    access_token: str,
    connect_timeout: int = 10,
) -> Engine:
    fields = SqlPasswordFields(
        host=host,
        port=port,
        database=database,
        username=username,
        password=access_token,
    )
    return create_mysql_engine(fields, ssl_mode="REQUIRED", connect_timeout=connect_timeout)


def create_postgresql_engine_with_rds_token(
    *,
    host: str,
    port: int,
    database: str,
    username: str,
    access_token: str,
    connect_timeout: int = 10,
) -> Engine:
    fields = SqlPasswordFields(
        host=host,
        port=port,
        database=database,
        username=username,
        password=access_token,
    )
    return create_postgresql_engine(fields, sslmode="require", connect_timeout=connect_timeout)


def create_mysql_engine_with_token(
    *,
    host: str,
    port: int,
    database: str,
    entra_user: str,
    access_token: str,
    connect_timeout: int = 10,
) -> Engine:
    fields = SqlPasswordFields(
        host=host,
        port=port,
        database=database,
        username=entra_user,
        password=access_token,
    )
    return create_mysql_engine(fields, ssl_enabled=True, connect_timeout=connect_timeout)


def create_postgresql_engine_with_token(
    *,
    host: str,
    port: int,
    database: str,
    entra_user: str,
    access_token: str,
    sslmode: str = "require",
    connect_timeout: int = 10,
) -> Engine:
    fields = SqlPasswordFields(
        host=host,
        port=port,
        database=database,
        username=entra_user,
        password=access_token,
    )
    return create_postgresql_engine(fields, sslmode=sslmode, connect_timeout=connect_timeout)


def create_mssql_engine_with_access_token(
    *,
    server: str,
    database: str,
    access_token: str,
    encrypt: bool = True,
    trust_server_certificate: bool = False,
    connect_timeout: int = 10,
) -> Engine:
    from config_platform_api.connectors.mssql_odbc import build_mssql_odbc_connect, create_mssql_engine

    odbc_connect = build_mssql_odbc_connect(
        server=server,
        port=1433,
        database=database,
        auth_method="sql_login",
        username="",
        password="",
        encrypt=encrypt,
        trust_server_certificate=trust_server_certificate,
    )
    return create_mssql_engine(odbc_connect, connect_timeout=connect_timeout, access_token=access_token)


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


def sanitize_connection_error(message: str) -> str:
    cleaned = strip_sqlalchemy_error_suffix(message)
    lowered = cleaned.lower()

    if "im002" in lowered or "data source name not found" in lowered:
        return (
            "Unable to connect to SQL Server. The ODBC driver is missing on the config API host. "
            "Install Microsoft ODBC Driver 18 for SQL Server and retry."
        )
    if "windows integrated security requires" in lowered:
        return cleaned
    if "password" in lowered or "access denied" in lowered or "login failed" in lowered:
        return "Connection failed. Check host, credentials, and network access."
    if "timeout" in lowered or "timed out" in lowered:
        return "Connection timed out. Check host, port, and firewall rules."
    if "could not connect" in lowered or "connection refused" in lowered:
        return "Unable to reach the database server. Check host, port, and network access."
    if "managed identity authentication failed" in lowered:
        return cleaned
    if "ssl" in lowered and "certificate" in lowered:
        return "TLS handshake failed. Review SSL settings and server certificates."
    if "nosuchbucket" in lowered or "accessdenied" in lowered or "invalidaccesskeyid" in lowered:
        return "S3 connection failed. Check bucket URI, region, and AWS credentials."
    if len(cleaned) > 240:
        return f"{cleaned[:237]}..."
    return cleaned
