"""Boto3 S3 client construction for csv_s3_bucket auth methods."""

from __future__ import annotations

from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config_platform_api.connectors.base import ConnectorValidationError
from config_platform_api.connectors.payloads import S3BucketConnectorPayload


def create_s3_client(payload: S3BucketConnectorPayload | dict[str, Any]):
    if isinstance(payload, dict):
        fields = S3BucketConnectorPayload.model_validate(payload)
    else:
        fields = payload

    region = fields.aws_region
    auth_method = fields.auth_method

    try:
        if auth_method == "access_key":
            return boto3.client(
                "s3",
                region_name=region,
                aws_access_key_id=fields.access_key_id,
                aws_secret_access_key=fields.secret_access_key,
            )
        if auth_method == "session_token":
            return boto3.client(
                "s3",
                region_name=region,
                aws_access_key_id=fields.access_key_id,
                aws_secret_access_key=fields.secret_access_key,
                aws_session_token=fields.session_token,
            )
        if auth_method == "instance_profile":
            return boto3.Session(region_name=region).client("s3")
        if auth_method == "assume_role":
            sts = boto3.client("sts", region_name=region)
            assume_kwargs: dict[str, str] = {
                "RoleArn": fields.role_arn,
                "RoleSessionName": "config-platform-s3-test",
            }
            if fields.external_id:
                assume_kwargs["ExternalId"] = fields.external_id
            assumed = sts.assume_role(**assume_kwargs)
            credentials = assumed["Credentials"]
            return boto3.client(
                "s3",
                region_name=region,
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
            )
    except (BotoCoreError, ClientError) as exc:
        raise ConnectorValidationError(f"Unable to create S3 client: {exc}") from exc

    raise ConnectorValidationError(f"Unsupported S3 auth method: {auth_method}")
