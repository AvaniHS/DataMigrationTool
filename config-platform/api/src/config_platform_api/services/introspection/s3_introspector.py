"""S3 file listing for CSV_S3_BUCKET connections."""

from urllib.parse import urlparse

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config_platform_api.models.connections import S3ConnectionFields
from config_platform_api.models.introspection import S3FileNode


def list_s3_files(fields: S3ConnectionFields) -> list[S3FileNode]:
    parsed = urlparse(fields.s3_bucket_uri)
    bucket = parsed.netloc
    prefix = parsed.path.lstrip("/")
    if not bucket:
        raise ValueError("S3 bucket URI must include a bucket name.")

    client = boto3.client("s3", region_name=fields.aws_region)
    files: list[S3FileNode] = []
    continuation_token: str | None = None

    try:
        while True:
            params: dict[str, object] = {"Bucket": bucket, "MaxKeys": 1000}
            if prefix:
                params["Prefix"] = prefix
            if continuation_token:
                params["ContinuationToken"] = continuation_token

            response = client.list_objects_v2(**params)
            for item in response.get("Contents", []):
                key = item["Key"]
                if key.endswith("/"):
                    continue
                name = key.rsplit("/", 1)[-1]
                if not name.lower().endswith(".csv"):
                    continue
                last_modified = item.get("LastModified")
                files.append(
                    S3FileNode(
                        name=name,
                        key=key,
                        size_bytes=item.get("Size"),
                        last_modified=last_modified.isoformat() if last_modified else None,
                    ),
                )

            if not response.get("IsTruncated"):
                break
            continuation_token = response.get("NextContinuationToken")
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(str(exc)) from exc

    return sorted(files, key=lambda item: item.name.lower())
