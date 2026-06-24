"""Shared connector payload models."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, populate_by_name=True)


class SqlPasswordFields(_StrictModel):
    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)
    database: str = Field(min_length=1)
    username: str = Field(min_length=1)
    password: str = ""
    use_advanced_string: bool = False
    connection_string: str | None = None


def sql_fields_from_dict(data: dict[str, object]) -> SqlPasswordFields:
    allowed = set(SqlPasswordFields.model_fields.keys())
    return SqlPasswordFields.model_validate({key: value for key, value in data.items() if key in allowed})


class MysqlConnectorPayload(_StrictModel):
    auth_method: Literal["password"] = "password"
    host: str = Field(min_length=1)
    port: int = Field(default=3306, ge=1, le=65535)
    database: str = Field(min_length=1)
    username: str = Field(min_length=1)
    password: str = ""
    use_advanced_string: bool = False
    connection_string: str | None = None


class PostgresqlConnectorPayload(_StrictModel):
    auth_method: Literal["password"] = "password"
    host: str = Field(min_length=1)
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = Field(min_length=1)
    username: str = Field(min_length=1)
    password: str = ""
    sslmode: str = "prefer"
    use_advanced_string: bool = False
    connection_string: str | None = None


class MssqlOnPremPayload(_StrictModel):
    auth_method: Literal["sql_login", "windows_integrated", "windows_login", "ntlm"] = "sql_login"
    host: str = Field(min_length=1)
    port: int = Field(default=1433, ge=1, le=65535)
    database: str = Field(min_length=1)
    username: str = ""
    password: str = ""
    domain: str = ""
    use_advanced_string: bool = False
    connection_string: str | None = None


class AzureSqlDatabasePayload(_StrictModel):
    auth_method: Literal[
        "sql_login",
        "entra_service_principal",
        "entra_password",
        "entra_managed_identity",
    ] = "sql_login"
    server: str = Field(min_length=1)
    database: str = Field(min_length=1)
    username: str = ""
    password: str = ""
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    use_advanced_string: bool = False
    connection_string: str | None = None


class S3BucketConnectorPayload(_StrictModel):
    auth_method: Literal["access_key", "session_token", "instance_profile", "assume_role"] = "access_key"
    s3_bucket_uri: str = Field(min_length=1)
    aws_region: str = Field(min_length=1)
    access_key_id: str = ""
    secret_access_key: str = ""
    session_token: str = ""
    role_arn: str = ""

    @field_validator("s3_bucket_uri")
    @classmethod
    def validate_s3_uri(cls, value: str) -> str:
        if not value.startswith("s3://"):
            raise ValueError("S3 bucket URI must start with s3://")
        return value


class LocalCsvConnectorPayload(_StrictModel):
    location_kind: Literal["local_path", "platform_staging"] = "local_path"
    file_path: str = ""
    staging_file_id: str = ""
    parse_options: dict[str, str | int] = Field(
        default_factory=lambda: {
            "delimiter": ",",
            "quote": '"',
            "header_row": 1,
            "encoding": "utf-8",
        },
    )
