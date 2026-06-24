"""Test connectivity for supported connection types."""

from dataclasses import dataclass

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy.engine import Engine
from urllib.parse import urlparse

from config_platform_api.logging_setup import get_logger
from config_platform_api.models.connections import ConnectionTestRequest, DatabaseConnectionFields
from config_platform_api.models.enums import ConnectionType
from config_platform_api.services.connection_engine import (
    create_database_engine,
    dispose_engine,
    verify_database_connection,
)

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
    engine: Engine | None = None
    try:
        engine = create_database_engine(connection_type, fields, connect_timeout=5)
        verify_database_connection(engine)
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
        dispose_engine(engine)


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
