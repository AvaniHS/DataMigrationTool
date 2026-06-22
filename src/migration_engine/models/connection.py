"""Connection configuration models."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from migration_engine.models.enums import ConnectionType


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", protected_namespaces=())


class DatabaseConnection(_FrozenModel):
    type: Literal[
        ConnectionType.MYSQL,
        ConnectionType.MSSQL,
        ConnectionType.POSTGRESQL,
    ]
    connection_string: str


class CsvS3Connection(_FrozenModel):
    type: Literal[ConnectionType.CSV_S3_BUCKET]
    s3_bucket_uri: str
    aws_region: str


ConnectionConfig = Annotated[
    DatabaseConnection | CsvS3Connection,
    Field(discriminator="type"),
]
