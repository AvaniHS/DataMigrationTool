"""Conflict strategy interface — implemented in Phase 2."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class InsertContext:
    """Inputs required to build a target INSERT statement."""

    target_schema: str
    target_table: str
    columns: list[str]
    projection_cte: str


class IConflictStrategy(ABC):
    """Builds INSERT statements for a specific on_conflict mode."""

    @abstractmethod
    def build_insert_statement(self, ctx: InsertContext) -> str:
        """Return the INSERT (or UPSERT) SQL fragment."""
