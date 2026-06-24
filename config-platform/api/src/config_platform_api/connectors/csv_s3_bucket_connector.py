"""Amazon S3 CSV bucket connector adapter."""

from typing import Any
from urllib.parse import urlparse

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import ValidationError

from config_platform_api.connectors.base import BaseConnector, ConnectorTestResult, ConnectorValidationError
from config_platform_api.connectors.payloads import S3BucketConnectorPayload
from config_platform_api.connectors.sql_helpers import sanitize_connection_error
from config_platform_api.logging_setup import get_logger
from config_platform_api.models.connectors import AuthMethodSchema
from config_platform_api.models.enums import ConnectionType

logger = get_logger(__name__)


class CsvS3BucketConnector(BaseConnector):
    connector_id = "csv_s3_bucket"
    label = "CSV on Amazon S3"
    description = "CSV files stored in an S3 bucket prefix."
    category = "file"
    export_type = ConnectionType.CSV_S3_BUCKET.value

    def auth_methods(self) -> list[AuthMethodSchema]:
        return [
            AuthMethodSchema(id="access_key", label="AWS access key", delivery_phase="P1.2"),
            AuthMethodSchema(id="session_token", label="Temporary credentials", delivery_phase="P1.4"),
            AuthMethodSchema(id="instance_profile", label="IAM role (API host)", delivery_phase="P1.4"),
            AuthMethodSchema(id="assume_role", label="Assume IAM role", delivery_phase="P1.4"),
        ]

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return S3BucketConnectorPayload.model_validate(payload).model_dump()
        except ValidationError as exc:
            raise ConnectorValidationError(str(exc)) from exc

    def _fingerprint_body(self, validated: dict[str, Any]) -> dict[str, Any]:
        return validated

    def test_connect(self, payload: dict[str, Any]) -> ConnectorTestResult:
        validated = self.validate(payload)
        return _test_s3_bucket(
            validated["s3_bucket_uri"],
            validated["aws_region"],
            validated["access_key_id"],
            validated["secret_access_key"],
        )

    def build_export(self, payload: dict[str, Any], *, secret_ref: str | None = None) -> dict[str, Any]:
        validated = self.validate(payload)
        exported: dict[str, Any] = {
            "type": self.export_type,
            "auth_method": validated["auth_method"],
            "s3_bucket_uri": validated["s3_bucket_uri"],
            "aws_region": validated["aws_region"],
            "access_key_id": validated["access_key_id"],
        }
        if secret_ref is not None:
            exported["secret_ref"] = secret_ref
        else:
            exported["secret_access_key"] = validated["secret_access_key"]
        return exported

    def build_summary(self, payload: dict[str, Any]) -> str:
        validated = self.validate(payload)
        return validated["s3_bucket_uri"]


def _test_s3_bucket(
    s3_bucket_uri: str,
    aws_region: str,
    access_key_id: str,
    secret_access_key: str,
) -> ConnectorTestResult:
    parsed = urlparse(s3_bucket_uri)
    bucket = parsed.netloc
    prefix = parsed.path.lstrip("/")
    if not bucket:
        return ConnectorTestResult(False, "S3 bucket URI must include a bucket name.")

    try:
        client = boto3.client(
            "s3",
            region_name=aws_region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )
        client.head_bucket(Bucket=bucket)
        if prefix:
            client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1)
        return ConnectorTestResult(True, f"S3 bucket '{bucket}' is reachable in {aws_region}.")
    except (BotoCoreError, ClientError) as exc:
        logger.warning(
            "csv_s3_bucket_connector_test_failed",
            bucket=bucket,
            aws_region=aws_region,
            error=str(exc),
            exc_info=True,
        )
        return ConnectorTestResult(False, sanitize_connection_error(str(exc)))
