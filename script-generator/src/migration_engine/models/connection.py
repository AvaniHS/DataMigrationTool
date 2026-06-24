"""Connection configuration models."""

from typing import Annotated, Any, Literal

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
    auth_method: str | None = None
    driver_options: dict[str, Any] | None = None
    entra: dict[str, str] | None = None
    aws: dict[str, str] | None = None
    secret_ref: str | None = None


class CsvS3Connection(_FrozenModel):
    type: Literal[ConnectionType.CSV_S3_BUCKET]
    s3_bucket_uri: str
    aws_region: str
    auth_method: str | None = None
    access_key_id: str | None = None
    secret_access_key: str | None = None
    session_token: str | None = None
    role_arn: str | None = None
    external_id: str | None = None
    secret_ref: str | None = None


ConnectionConfig = Annotated[
    DatabaseConnection | CsvS3Connection,
    Field(discriminator="type"),
]
