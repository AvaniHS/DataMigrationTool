"""Unit tests for S3 file column sample introspection."""

from unittest.mock import MagicMock, patch

import pytest

from config_platform_api.connectors.payloads import S3BucketConnectorPayload
from config_platform_api.models.introspection import S3FileNode
from config_platform_api.services.introspection import s3_introspector


def test_list_s3_file_columns_parses_header_sample() -> None:
    payload = S3BucketConnectorPayload(
        auth_method="access_key",
        s3_bucket_uri="s3://bucket/prefix/",
        aws_region="us-east-1",
        access_key_id="AKIA",
        secret_access_key="secret",
    )
    mock_client = MagicMock()
    mock_client.get_object.return_value = {
        "Body": MagicMock(read=lambda: b"id,name\n1,Alice\n"),
    }

    with (
        patch.object(
            s3_introspector,
            "list_s3_files",
            return_value=[S3FileNode(name="data.csv", key="prefix/data.csv")],
        ),
        patch.object(s3_introspector, "create_s3_client", return_value=mock_client),
    ):
        columns = s3_introspector.list_s3_file_columns(payload, "data.csv")

    assert [column.name for column in columns] == ["id", "name"]
