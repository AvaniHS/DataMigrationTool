"""AWS RDS IAM database authentication token helpers."""

from __future__ import annotations

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config_platform_api.connectors.base import ConnectorValidationError


def generate_rds_auth_token(*, host: str, port: int, username: str, region: str) -> str:
    if not region:
        raise ConnectorValidationError("aws_region is required for RDS IAM authentication.")
    try:
        client = boto3.client("rds", region_name=region)
        return client.generate_db_auth_token(
            DBHostname=host,
            Port=port,
            DBUsername=username,
            Region=region,
        )
    except (BotoCoreError, ClientError) as exc:
        raise ConnectorValidationError(
            f"Unable to generate RDS IAM auth token. Check AWS credentials and IAM permissions: {exc}"
        ) from exc
