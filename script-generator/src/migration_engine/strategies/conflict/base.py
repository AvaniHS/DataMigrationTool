"""Conflict strategy interface and shared insert context."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class InsertContext:
    """Inputs required to build a target INSERT statement."""

    target_schema: str
    target_table: str
    columns: list[str]
    projection_cte: str
    primary_keys: list[str] = field(default_factory=list)
    audit_table: str | None = None
    unprocessed_table: str | None = None


class IConflictStrategy(ABC):
    """Builds INSERT statements for a specific on_conflict mode."""

    @abstractmethod
    def build_insert_statement(self, ctx: InsertContext) -> str:
        """Return the INSERT (or UPSERT) SQL fragment."""
