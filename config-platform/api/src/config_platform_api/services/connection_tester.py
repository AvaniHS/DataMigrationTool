"""Test connectivity for supported connection types."""

from dataclasses import dataclass
from urllib.parse import urlparse

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL, make_url

from config_platform_api.logging_setup import get_logger
from config_platform_api.models.connections import ConnectionTestRequest, DatabaseConnectionFields
from config_platform_api.models.enums import ConnectionType
from config_platform_api.services.connection_builder import build_database_connection_string

logger = get_logger(__name__)


@dataclass(frozen=True)
class TestResult:
    success: bool
    message: str


def test_connection(request: ConnectionTestRequest) -> TestResult:
    if request.type == ConnectionType.CSV_S3_BUCKET:
        if request.s3 is None:
            return TestResult(False, "S3 fields are required.")
        return _test_s3(request.s3.s3_bucket_uri, request.s3.aws_region)

    if request.database is None:
        return TestResult(False, "Database fields are required.")

    return _test_database(request.type, request.database)


def _test_database(connection_type: ConnectionType, fields: DatabaseConnectionFields) -> TestResult:
    connection_string = build_database_connection_string(connection_type, fields)
    engine: Engine | None = None
    try:
        url = _to_sqlalchemy_url(connection_type, connection_string)
        engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        summary = f"{fields.host}:{fields.port}/{fields.database}"
        return TestResult(True, f"Connected successfully to {summary}.")
    except Exception as exc:
        logger.warning(
            "database_connection_test_failed",
            connection_type=connection_type.value,
            host=fields.host,
            database=fields.database,
            error=str(exc),
            exc_info=True,
        )
        return TestResult(False, _sanitize_error(str(exc)))
    finally:
        if engine is not None:
            engine.dispose()


def _to_sqlalchemy_url(connection_type: ConnectionType, connection_string: str) -> URL:
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


def _test_s3(s3_bucket_uri: str, aws_region: str) -> TestResult:
    parsed = urlparse(s3_bucket_uri)
    bucket = parsed.netloc
    prefix = parsed.path.lstrip("/")
    if not bucket:
        return TestResult(False, "S3 bucket URI must include a bucket name.")

    try:
        client = boto3.client("s3", region_name=aws_region)
        client.head_bucket(Bucket=bucket)
        if prefix:
            client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1)
        return TestResult(True, f"S3 bucket '{bucket}' is reachable in {aws_region}.")
    except (BotoCoreError, ClientError) as exc:
        logger.warning(
            "s3_connection_test_failed",
            bucket=bucket,
            aws_region=aws_region,
            error=str(exc),
            exc_info=True,
        )
        return TestResult(False, _sanitize_error(str(exc)))


def _sanitize_error(message: str) -> str:
    lowered = message.lower()
    if "password" in lowered or "access denied" in lowered:
        return "Connection failed. Check host, credentials, and network access."
    if len(message) > 240:
        return f"{message[:237]}..."
    return message
