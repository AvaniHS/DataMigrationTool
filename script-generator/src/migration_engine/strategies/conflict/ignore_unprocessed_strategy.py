"""IGNORE_AND_INSERT_UNPROCESSED conflict strategy."""

from migration_engine.dialects.base_dialect import BaseDialect
from migration_engine.strategies.conflict._statement_builder import (
    build_insert_into,
    build_preinsert_conflict_capture,
)
from migration_engine.strategies.conflict.base import IConflictStrategy, InsertContext


class IgnoreUnprocessedStrategy(IConflictStrategy):
    """Routes conflicting rows to an unprocessed table, then INSERT IGNORE."""

    def __init__(self, dialect: BaseDialect) -> None:
        self._dialect = dialect

    def build_insert_statement(self, ctx: InsertContext) -> str:
        if not ctx.primary_keys:
            raise ValueError(
                "IGNORE_AND_INSERT_UNPROCESSED requires at least one primary key column."
            )
        if not ctx.unprocessed_table:
            raise ValueError(
                "IGNORE_AND_INSERT_UNPROCESSED requires target.unprocessed_table in config."
            )

        capture = build_preinsert_conflict_capture(
            self._dialect, ctx, ctx.unprocessed_table
        )
        insert = build_insert_into(self._dialect, ctx, ignore=True)
        return f"{capture};\n\n{insert};"
