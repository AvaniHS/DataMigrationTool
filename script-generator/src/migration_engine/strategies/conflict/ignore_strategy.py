"""IGNORE conflict strategy — INSERT IGNORE."""

from migration_engine.dialects.base_dialect import BaseDialect
from migration_engine.strategies.conflict._statement_builder import build_insert_into
from migration_engine.strategies.conflict.base import IConflictStrategy, InsertContext


class IgnoreStrategy(IConflictStrategy):
    """Silently skips rows that violate unique constraints."""

    def __init__(self, dialect: BaseDialect) -> None:
        self._dialect = dialect

    def build_insert_statement(self, ctx: InsertContext) -> str:
        return build_insert_into(self._dialect, ctx, ignore=True)
