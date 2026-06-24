"""Local CSV file introspection."""

from __future__ import annotations

from pathlib import Path

from config_platform_api.models.introspection import ColumnNode, S3FileNode
from config_platform_api.services.local_csv.csv_sample import read_csv_column_names


def list_local_csv_files(path: Path) -> list[S3FileNode]:
    stat = path.stat()
    return [
        S3FileNode(
            name=path.name,
            key=path.name,
            size_bytes=stat.st_size,
            last_modified=None,
        ),
    ]


def list_local_csv_columns(path: Path, parse_options: dict[str, str | int]) -> list[ColumnNode]:
    names = read_csv_column_names(path, parse_options)
    return [ColumnNode(name=name, data_type="string", is_nullable=True) for name in names]
