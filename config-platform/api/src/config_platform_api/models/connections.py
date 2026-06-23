from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from config_platform_api.models.enums import ConnectionType


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class DatabaseConnectionFields(_StrictModel):
    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)
    database: str = Field(min_length=1)
    username: str = Field(min_length=1)
    password: str = ""
    use_advanced_string: bool = False
    connection_string: str | None = None


class S3ConnectionFields(_StrictModel):
    s3_bucket_uri: str = Field(min_length=1)
    aws_region: str = Field(min_length=1)

    @field_validator("s3_bucket_uri")
    @classmethod
    def validate_s3_uri(cls, value: str) -> str:
        if not value.startswith("s3://"):
            raise ValueError("S3 bucket URI must start with s3://")
        return value


class ConnectionPayload(_StrictModel):
    """Structured connection input from the UI."""

    ref: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    type: ConnectionType
    secret_ref: str | None = None
    database: DatabaseConnectionFields | None = None
    s3: S3ConnectionFields | None = None

    @field_validator("ref")
    @classmethod
    def normalize_ref(cls, value: str) -> str:
        return value.strip().lower()


class ConnectionRecord(ConnectionPayload):
    created_at: datetime
    updated_at: datetime
    last_tested_at: datetime | None = None


class ConnectionTestRequest(_StrictModel):
    type: ConnectionType
    database: DatabaseConnectionFields | None = None
    s3: S3ConnectionFields | None = None


class ConnectionTestResponse(_StrictModel):
    success: bool
    message: str
    verification_token: str | None = None


class ConnectionSaveRequest(ConnectionPayload):
    verification_token: str = Field(min_length=1)


class ExportedDatabaseConnection(_StrictModel):
    type: Literal[ConnectionType.MYSQL, ConnectionType.MSSQL, ConnectionType.POSTGRESQL]
    connection_string: str


class ExportedS3Connection(_StrictModel):
    type: Literal[ConnectionType.CSV_S3_BUCKET]
    s3_bucket_uri: str
    aws_region: str


class ConnectionListItem(_StrictModel):
    ref: str
    type: ConnectionType
    summary: str
    last_tested_at: datetime | None
    updated_at: datetime
