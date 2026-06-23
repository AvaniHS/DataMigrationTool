"""UPSERT conflict strategy — ON DUPLICATE KEY UPDATE."""

from migration_engine.dialects.base_dialect import BaseDialect
from migration_engine.strategies.conflict._statement_builder import build_insert_into
from migration_engine.strategies.conflict.base import IConflictStrategy, InsertContext


class UpsertStrategy(IConflictStrategy):
    """Updates existing rows when a primary key conflict occurs."""

    def __init__(self, dialect: BaseDialect) -> None:
        self._dialect = dialect

    def build_insert_statement(self, ctx: InsertContext) -> str:
        if not ctx.primary_keys:
            raise ValueError("UPSERT requires at least one primary key column.")

        return build_insert_into(self._dialect, ctx, upsert=True)
