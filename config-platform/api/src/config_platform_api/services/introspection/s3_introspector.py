"""S3 file listing for CSV_S3_BUCKET connections."""

from urllib.parse import urlparse

from botocore.exceptions import BotoCoreError, ClientError

from config_platform_api.connectors.payloads import S3BucketConnectorPayload
from config_platform_api.connectors.s3_auth import create_s3_client
from config_platform_api.models.introspection import ColumnNode, S3FileNode
from config_platform_api.services.local_csv.csv_sample import (
    DEFAULT_PARSE_OPTIONS,
    read_csv_column_names_from_text,
)

SAMPLE_BYTES = 65_536


def list_s3_files(fields: S3BucketConnectorPayload) -> list[S3FileNode]:
    parsed = urlparse(fields.s3_bucket_uri)
    bucket = parsed.netloc
    prefix = parsed.path.lstrip("/")
    if not bucket:
        raise ValueError("S3 bucket URI must include a bucket name.")

    client = create_s3_client(fields)
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


def list_s3_file_columns(fields: S3BucketConnectorPayload, file_name: str) -> list[ColumnNode]:
    parsed = urlparse(fields.s3_bucket_uri)
    bucket = parsed.netloc
    if not bucket:
        raise ValueError("S3 bucket URI must include a bucket name.")

    files = list_s3_files(fields)
    match = next((item for item in files if item.name == file_name), None)
    if match is None:
        raise ValueError(f"File '{file_name}' was not found for this connection.")

    client = create_s3_client(fields)
    try:
        response = client.get_object(
            Bucket=bucket,
            Key=match.key,
            Range=f"bytes=0-{SAMPLE_BYTES - 1}",
        )
        raw = response["Body"].read()
        sample = raw.decode("utf-8", errors="replace")
        names = read_csv_column_names_from_text(sample, DEFAULT_PARSE_OPTIONS)
        return [ColumnNode(name=name, data_type="string", is_nullable=True) for name in names]
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(str(exc)) from exc
