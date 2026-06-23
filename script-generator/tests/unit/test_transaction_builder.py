"""Unit tests for transaction builder."""

from migration_engine.compilers.transaction_builder import TransactionBuilder
from migration_engine.dialects.mysql_dialect import MySqlDialect


def test_wrap_blueprint_block_includes_transaction_and_savepoint() -> None:
    builder = TransactionBuilder(MySqlDialect())
    wrapped = builder.wrap_blueprint_block(1, "SELECT 1;")

    assert wrapped.startswith("START TRANSACTION;")
    assert "SAVEPOINT bp_step_1;" in wrapped
    assert "SELECT 1;" in wrapped
    assert "RELEASE SAVEPOINT bp_step_1;" in wrapped
    assert wrapped.endswith("COMMIT;")
