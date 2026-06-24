"""Validation report models."""

from pydantic import BaseModel, ConfigDict, Field


class ValidationIssueResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    path: str = ""
    blueprint_sequence: int | None = None


class ValidationReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    migration_id: str
    is_valid: bool
    issue_count: int = Field(ge=0)
    issues: list[ValidationIssueResponse] = Field(default_factory=list)
