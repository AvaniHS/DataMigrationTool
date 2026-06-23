"""FAIL conflict strategy — plain INSERT."""

from migration_engine.dialects.base_dialect import BaseDialect
from migration_engine.strategies.conflict._statement_builder import build_insert_into
from migration_engine.strategies.conflict.base import IConflictStrategy, InsertContext


class FailStrategy(IConflictStrategy):
    """Raises on duplicate key by using a plain INSERT."""

    def __init__(self, dialect: BaseDialect) -> None:
        self._dialect = dialect

    def build_insert_statement(self, ctx: InsertContext) -> str:
        return build_insert_into(self._dialect, ctx)
