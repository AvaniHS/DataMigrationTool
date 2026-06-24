"""Shared connector payload models."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ENTRA_SERVICE_PRINCIPAL = "entra_service_principal"
ENTRA_PASSWORD = "entra_password"
ENTRA_MANAGED_IDENTITY = "entra_managed_identity"


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


def _require_non_empty(value: str, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} is required for this auth method")


class MysqlConnectorPayload(_StrictModel):
    auth_method: Literal["password", ENTRA_SERVICE_PRINCIPAL, ENTRA_MANAGED_IDENTITY] = "password"
    host: str = Field(min_length=1)
    port: int = Field(default=3306, ge=1, le=65535)
    database: str = Field(min_length=1)
    username: str = ""
    password: str = ""
    ssl_enabled: bool = False
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    entra_user: str = ""
    managed_identity_client_id: str = ""
    use_advanced_string: bool = False
    connection_string: str | None = None

    @model_validator(mode="after")
    def validate_auth_fields(self) -> Self:
        if self.auth_method == "password":
            _require_non_empty(self.username, "username")
        if self.auth_method == ENTRA_SERVICE_PRINCIPAL:
            _require_non_empty(self.tenant_id, "tenant_id")
            _require_non_empty(self.client_id, "client_id")
            _require_non_empty(self.client_secret, "client_secret")
            _require_non_empty(self.entra_user, "entra_user")
        if self.auth_method == ENTRA_MANAGED_IDENTITY:
            _require_non_empty(self.entra_user, "entra_user")
        return self


class PostgresqlConnectorPayload(_StrictModel):
    auth_method: Literal[
        "password",
        ENTRA_PASSWORD,
        ENTRA_SERVICE_PRINCIPAL,
        ENTRA_MANAGED_IDENTITY,
    ] = "password"
    host: str = Field(min_length=1)
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = Field(min_length=1)
    username: str = ""
    password: str = ""
    sslmode: Literal["disable", "allow", "prefer", "require", "verify-ca", "verify-full"] = "prefer"
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    entra_user: str = ""
    entra_password: str = ""
    managed_identity_client_id: str = ""
    use_advanced_string: bool = False
    connection_string: str | None = None

    @model_validator(mode="after")
    def validate_auth_fields(self) -> Self:
        if self.auth_method == "password":
            _require_non_empty(self.username, "username")
        if self.auth_method == ENTRA_PASSWORD:
            _require_non_empty(self.tenant_id, "tenant_id")
            _require_non_empty(self.client_id, "client_id")
            _require_non_empty(self.entra_user, "entra_user")
            _require_non_empty(self.entra_password, "entra_password")
        if self.auth_method == ENTRA_SERVICE_PRINCIPAL:
            _require_non_empty(self.tenant_id, "tenant_id")
            _require_non_empty(self.client_id, "client_id")
            _require_non_empty(self.client_secret, "client_secret")
            _require_non_empty(self.entra_user, "entra_user")
        if self.auth_method == ENTRA_MANAGED_IDENTITY:
            _require_non_empty(self.entra_user, "entra_user")
        return self


class MssqlOnPremPayload(_StrictModel):
    auth_method: Literal["sql_login", "windows_integrated", "windows_login", "ntlm"] = "sql_login"
    host: str = Field(min_length=1)
    port: int = Field(default=1433, ge=1, le=65535)
    database: str = Field(min_length=1)
    username: str = ""
    password: str = ""
    domain: str = ""
    encrypt: bool = True
    trust_server_certificate: bool = False
    use_advanced_string: bool = False
    connection_string: str | None = None

    @model_validator(mode="after")
    def validate_auth_fields(self) -> Self:
        if self.auth_method == "ntlm":
            raise ValueError("ntlm auth is available in P1.4.")
        if self.auth_method == "sql_login" and not self.username:
            raise ValueError("username is required for sql_login")
        if self.auth_method == "windows_login":
            if not self.username:
                raise ValueError("username is required for windows_login")
            if not self.domain:
                raise ValueError("domain is required for windows_login")
        return self


class AzureSqlDatabasePayload(_StrictModel):
    auth_method: Literal[
        "sql_login",
        ENTRA_SERVICE_PRINCIPAL,
        ENTRA_PASSWORD,
        ENTRA_MANAGED_IDENTITY,
    ] = "sql_login"
    server: str = Field(min_length=1)
    database: str = Field(min_length=1)
    username: str = ""
    password: str = ""
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    entra_user: str = ""
    entra_password: str = ""
    managed_identity_client_id: str = ""
    encrypt: bool = True
    trust_server_certificate: bool = False
    use_advanced_string: bool = False
    connection_string: str | None = None

    @model_validator(mode="after")
    def validate_auth_fields(self) -> Self:
        if self.auth_method == "sql_login":
            _require_non_empty(self.username, "username")
        if self.auth_method == ENTRA_SERVICE_PRINCIPAL:
            _require_non_empty(self.tenant_id, "tenant_id")
            _require_non_empty(self.client_id, "client_id")
            _require_non_empty(self.client_secret, "client_secret")
        if self.auth_method == ENTRA_PASSWORD:
            _require_non_empty(self.tenant_id, "tenant_id")
            _require_non_empty(self.client_id, "client_id")
            _require_non_empty(self.entra_user, "entra_user")
            _require_non_empty(self.entra_password, "entra_password")
        return self


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

    @model_validator(mode="after")
    def validate_auth_fields(self) -> Self:
        if self.auth_method != "access_key":
            raise ValueError(f"{self.auth_method} is available in P1.4.")
        if not self.access_key_id:
            raise ValueError("access_key_id is required for access_key auth")
        if not self.secret_access_key:
            raise ValueError("secret_access_key is required for access_key auth")
        return self


class LocalCsvParseOptions(_StrictModel):
    delimiter: str = ","
    quote: str = '"'
    header_row: int = Field(default=1, ge=1)
    encoding: str = "utf-8"

    @field_validator("delimiter", "quote")
    @classmethod
    def single_character(cls, value: str) -> str:
        if len(value) != 1:
            raise ValueError("delimiter and quote must be a single character")
        return value


class LocalCsvConnectorPayload(_StrictModel):
    location_kind: Literal["local_path", "platform_staging"] = "local_path"
    file_path: str = ""
    staging_file_id: str = ""
    parse_options: LocalCsvParseOptions = Field(default_factory=LocalCsvParseOptions)

    @model_validator(mode="after")
    def validate_location_fields(self) -> Self:
        if self.location_kind == "local_path":
            _require_non_empty(self.file_path, "file_path")
        if self.location_kind == "platform_staging":
            _require_non_empty(self.staging_file_id, "staging_file_id")
        return self
