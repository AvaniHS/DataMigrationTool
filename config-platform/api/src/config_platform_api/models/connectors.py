from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ConnectorCategory = Literal["database", "file"]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AuthMethodSchema(_StrictModel):
    id: str
    label: str
    delivery_phase: str = Field(description="e.g. P1.2 — shown in UI for tiered auth")


class ConnectorMetadata(_StrictModel):
    connector_id: str
    label: str
    description: str
    category: ConnectorCategory
    export_type: str
    auth_methods: list[AuthMethodSchema] = Field(default_factory=list)


class ConnectorSchemaResponse(_StrictModel):
    connector_id: str
    export_type: str
    category: ConnectorCategory
    auth_methods: list[AuthMethodSchema]
    payload_hint: dict[str, Any] = Field(default_factory=dict)
