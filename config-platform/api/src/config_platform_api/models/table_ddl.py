"""Target DDL request/response models (P6)."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CopyStructureMode(str, Enum):
    COPY_FROM_TABLE = "COPY_FROM_TABLE"
    AUDIT_TABLE = "AUDIT_TABLE"


class TableColumnSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    data_type: str = Field(min_length=1)
    is_nullable: bool = True


class CopyStructureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: CopyStructureMode
    destination_schema: str = Field(min_length=1)
    destination_table: str = Field(min_length=1)
    source_schema: str | None = None
    source_table: str | None = None
    migration_id: str | None = None
    blueprint_sequence: int | None = Field(default=None, ge=1)
    target_schema: str | None = None
    target_table: str | None = None
    primary_key_columns: list[str] = Field(default_factory=list)
    target_columns: list[TableColumnSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_mode_fields(self) -> "CopyStructureRequest":
        if self.mode == CopyStructureMode.COPY_FROM_TABLE:
            if not self.source_schema or not self.source_table:
                raise ValueError("source_schema and source_table are required for COPY_FROM_TABLE.")
            return self

        if not self.migration_id:
            raise ValueError("migration_id is required for AUDIT_TABLE.")
        if self.blueprint_sequence is None:
            raise ValueError("blueprint_sequence is required for AUDIT_TABLE.")
        if not self.target_schema or not self.target_table:
            raise ValueError("target_schema and target_table are required for AUDIT_TABLE.")
        if not self.primary_key_columns:
            raise ValueError("primary_key_columns are required for AUDIT_TABLE.")
        if not self.target_columns:
            raise ValueError("target_columns are required for AUDIT_TABLE.")
        return self


class CopyStructureResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connection_ref: str
    mode: CopyStructureMode
    qualified_name: str
    created: bool
    skipped_existing: bool = False
    message: str
