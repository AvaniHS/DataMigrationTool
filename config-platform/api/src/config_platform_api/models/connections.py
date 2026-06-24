from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ConnectionPayload(_StrictModel):
    """Structured connection input from the UI."""

    ref: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    connector_id: str = Field(min_length=1)
    connector_payload: dict[str, Any] = Field(default_factory=dict)
    secret_ref: str | None = None

    @field_validator("ref")
    @classmethod
    def normalize_ref(cls, value: str) -> str:
        return value.strip().lower()


class ConnectionRecord(ConnectionPayload):
    created_at: datetime
    updated_at: datetime
    last_tested_at: datetime | None = None


class ConnectionTestRequest(_StrictModel):
    connector_id: str = Field(min_length=1)
    connector_payload: dict[str, Any] = Field(default_factory=dict)


class ConnectionTestResponse(_StrictModel):
    success: bool
    message: str
    verification_token: str | None = None


class ConnectionSaveRequest(ConnectionPayload):
    verification_token: str = Field(min_length=1)


class ConnectionListItem(_StrictModel):
    ref: str
    connector_id: str
    export_type: str
    category: str
    summary: str
    last_tested_at: datetime | None
    updated_at: datetime
