from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from config_platform_api.models.enums import OnConflictStrategy

_OUTPUT_FORMAT = Literal["SQL"]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, populate_by_name=True)


class ChunkingStrategy(_StrictModel):
    is_enabled: bool = False
    chunk_by_column: str | None = None
    chunk_size: int | None = None


class BlueprintTarget(_StrictModel):
    connection_ref: str = ""
    schema_name: str = Field(default="", alias="schema")
    table_name: str = ""
    primary_keys: list[str] = Field(default_factory=list)
    on_conflict: OnConflictStrategy = OnConflictStrategy.FAIL
    unprocessed_table: str | None = None
    audit_table: str | None = None


class RootTableSource(_StrictModel):
    connection_ref: str = ""
    alias: str = "src"
    schema_name: str = Field(default="", alias="schema")
    table_name: str = ""
    file_name: str | None = None
    comment: str | None = None


class JoinCondition(_StrictModel):
    left_expression: str
    operator: str
    right_expression: str


class JoinSource(_StrictModel):
    join_type: Literal["INNER", "LEFT", "RIGHT", "FULL"] = "LEFT"
    connection_ref: str = ""
    alias: str = ""
    schema_name: str = Field(default="", alias="schema")
    table_name: str = ""
    file_name: str | None = None
    comment: str | None = None
    conditions: list[JoinCondition] = Field(default_factory=list)


class BlueprintSources(_StrictModel):
    root_table: RootTableSource = Field(default_factory=RootTableSource)
    joins: list[JoinSource] = Field(default_factory=list)


class Derivation(_StrictModel):
    variable_name: str
    expression: str


class ColumnMapping(_StrictModel):
    target_column: str
    source_type: Literal["DIRECT", "DERIVED", "EXPRESSION", "CONSTANT"]
    source_value: str
    cast_to: str
    is_nullable: bool


class Blueprint(_StrictModel):
    sequence_order: int = Field(ge=1)
    target: BlueprintTarget = Field(default_factory=BlueprintTarget)
    sources: BlueprintSources = Field(default_factory=BlueprintSources)
    chunking_strategy: ChunkingStrategy = Field(default_factory=ChunkingStrategy)
    pre_filters: list[str] = Field(default_factory=list)
    post_filters: list[str] = Field(default_factory=list)
    derivations: list[Derivation] = Field(default_factory=list)
    mappings: list[ColumnMapping] = Field(default_factory=list)


class MigrationHeader(_StrictModel):
    migration_id: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    client_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    output_format: _OUTPUT_FORMAT = "SQL"

    @field_validator("migration_id")
    @classmethod
    def normalize_migration_id(cls, value: str) -> str:
        return value.strip().lower()


class MigrationRecord(MigrationHeader):
    blueprints: list[Blueprint] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class MigrationListItem(_StrictModel):
    migration_id: str
    client_id: str
    version: str
    output_format: _OUTPUT_FORMAT
    blueprint_count: int = Field(ge=0)
    updated_at: datetime


class CreateMigrationRequest(MigrationHeader):
    pass


class UpdateMigrationRequest(_StrictModel):
    client_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    blueprints: list[Blueprint] = Field(default_factory=list)


class ReorderBlueprintsRequest(_StrictModel):
    sequence_orders: list[int] = Field(min_length=1)
