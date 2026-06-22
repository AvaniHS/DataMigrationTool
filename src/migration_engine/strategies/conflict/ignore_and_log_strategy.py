"""IGNORE_AND_LOG conflict strategy."""

from migration_engine.dialects.base_dialect import BaseDialect
from migration_engine.strategies.conflict._statement_builder import (
    build_insert_into,
    build_preinsert_conflict_capture,
)
from migration_engine.strategies.conflict.base import IConflictStrategy, InsertContext

_DEFAULT_AUDIT_TABLE = "migration_conflict_log"


class IgnoreAndLogStrategy(IConflictStrategy):
    """Logs conflicting rows, then inserts new rows with INSERT IGNORE."""

    def __init__(self, dialect: BaseDialect) -> None:
        self._dialect = dialect

    def build_insert_statement(self, ctx: InsertContext) -> str:
        if not ctx.primary_keys:
            raise ValueError("IGNORE_AND_LOG requires at least one primary key column.")

        audit_table = ctx.audit_table or _DEFAULT_AUDIT_TABLE
        capture = build_preinsert_conflict_capture(self._dialect, ctx, audit_table)
        insert = build_insert_into(self._dialect, ctx, ignore=True)
        return f"{capture};\n\n{insert};"
