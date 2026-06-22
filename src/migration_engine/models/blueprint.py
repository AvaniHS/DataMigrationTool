"""Blueprint and migration DTO models."""

from pydantic import BaseModel, ConfigDict, Field

from migration_engine.models.connection import ConnectionConfig
from migration_engine.models.enums import ConflictStrategy, JoinType, OutputFormat
from migration_engine.models.mapping import ColumnMapping, Derivation, JoinCondition


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", protected_namespaces=())


class ChunkingStrategy(_FrozenModel):
    is_enabled: bool
    chunk_by_column: str | None = None
    chunk_size: int | None = None


class TargetDefinition(_FrozenModel):
    connection_ref: str
    schema: str
    table_name: str
    primary_keys: list[str]
    on_conflict: ConflictStrategy
    comment: str | None = None
    unprocessed_table: str | None = None


class TableSource(_FrozenModel):
    connection_ref: str
    schema: str
    table_name: str
    alias: str
    comment: str | None = None


class FileSource(_FrozenModel):
    connection_ref: str
    file_name: str
    alias: str
    comment: str | None = None


class TableJoin(_FrozenModel):
    join_type: JoinType
    connection_ref: str
    schema: str
    table_name: str
    alias: str
    conditions: list[JoinCondition]
    comment: str | None = None


class FileJoin(_FrozenModel):
    join_type: JoinType
    connection_ref: str
    file_name: str
    alias: str
    conditions: list[JoinCondition]
    comment: str | None = None


RootSource = TableSource | FileSource
JoinSource = TableJoin | FileJoin


class SourcesDefinition(_FrozenModel):
    root_table: RootSource
    joins: list[JoinSource] = Field(default_factory=list)


class Blueprint(_FrozenModel):
    sequence_order: int
    target: TargetDefinition
    sources: SourcesDefinition
    chunking_strategy: ChunkingStrategy
    pre_filters: list[str] = Field(default_factory=list)
    derivations: list[Derivation] = Field(default_factory=list)
    post_filters: list[str] = Field(default_factory=list)
    mappings: list[ColumnMapping]


class MasterMigrationBlueprint(_FrozenModel):
    migration_id: str
    client_id: str
    version: str
    output_format: OutputFormat = OutputFormat.SQL
    connections: dict[str, ConnectionConfig]
    blueprints: list[Blueprint]
