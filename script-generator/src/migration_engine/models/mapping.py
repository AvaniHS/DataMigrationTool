"""Column mapping and join models."""

from pydantic import BaseModel, ConfigDict

from migration_engine.models.enums import JoinType, SourceType


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", protected_namespaces=())


class JoinCondition(_FrozenModel):
    left_expression: str
    operator: str
    right_expression: str


class ColumnMapping(_FrozenModel):
    target_column: str
    source_type: SourceType
    source_value: str
    cast_to: str
    is_nullable: bool


class Derivation(_FrozenModel):
    variable_name: str
    expression: str
