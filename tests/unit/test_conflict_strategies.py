"""Unit tests for conflict strategies."""

import pytest

from migration_engine.dialects.mysql_dialect import MySqlDialect
from migration_engine.factories.conflict_strategy_factory import ConflictStrategyFactory
from migration_engine.models.enums import ConflictStrategy
from migration_engine.strategies.conflict.base import InsertContext


@pytest.fixture
def dialect() -> MySqlDialect:
    return MySqlDialect()


@pytest.fixture
def insert_context() -> InsertContext:
    return InsertContext(
        target_schema="core",
        target_table="customers",
        columns=["id", "company_name", "phone"],
        projection_cte="bp1_target_projection",
        primary_keys=["id"],
    )


def test_factory_registers_all_strategies() -> None:
    supported = ConflictStrategyFactory.supported_strategies()
    assert supported == frozenset(
        {
            ConflictStrategy.FAIL.value,
            ConflictStrategy.IGNORE.value,
            ConflictStrategy.UPSERT.value,
            ConflictStrategy.IGNORE_AND_LOG.value,
            ConflictStrategy.IGNORE_AND_INSERT_UNPROCESSED.value,
        }
    )


def test_fail_strategy_builds_plain_insert(
    dialect: MySqlDialect, insert_context: InsertContext
) -> None:
    strategy = ConflictStrategyFactory.create(ConflictStrategy.FAIL.value, dialect)
    sql = strategy.build_insert_statement(insert_context)

    assert sql.startswith("INSERT INTO core.customers (id, company_name, phone)")
    assert "SELECT id, company_name, phone" in sql
    assert "FROM bp1_target_projection" in sql
    assert "IGNORE" not in sql
    assert "ON DUPLICATE KEY UPDATE" not in sql


def test_ignore_strategy_builds_insert_ignore(
    dialect: MySqlDialect, insert_context: InsertContext
) -> None:
    strategy = ConflictStrategyFactory.create(ConflictStrategy.IGNORE.value, dialect)
    sql = strategy.build_insert_statement(insert_context)

    assert sql.startswith("INSERT IGNORE INTO core.customers")


def test_upsert_strategy_builds_on_duplicate_key_update(
    dialect: MySqlDialect, insert_context: InsertContext
) -> None:
    strategy = ConflictStrategyFactory.create(ConflictStrategy.UPSERT.value, dialect)
    sql = strategy.build_insert_statement(insert_context)

    assert "INSERT INTO core.customers" in sql
    assert "ON DUPLICATE KEY UPDATE company_name = VALUES(company_name)" in sql


def test_upsert_requires_primary_keys(dialect: MySqlDialect) -> None:
    strategy = ConflictStrategyFactory.create(ConflictStrategy.UPSERT.value, dialect)
    context = InsertContext(
        target_schema="core",
        target_table="customers",
        columns=["id"],
        projection_cte="bp1_target_projection",
        primary_keys=[],
    )

    with pytest.raises(ValueError, match="primary key"):
        strategy.build_insert_statement(context)


def test_ignore_and_log_strategy_captures_conflicts_first(
    dialect: MySqlDialect, insert_context: InsertContext
) -> None:
    strategy = ConflictStrategyFactory.create(ConflictStrategy.IGNORE_AND_LOG.value, dialect)
    sql = strategy.build_insert_statement(insert_context)

    assert "INSERT INTO core.migration_conflict_log" in sql
    assert "INNER JOIN core.customers t ON p.id = t.id" in sql
    assert "INSERT IGNORE INTO core.customers" in sql
    assert sql.index("migration_conflict_log") < sql.index("INSERT IGNORE")


def test_ignore_and_log_uses_custom_audit_table(
    dialect: MySqlDialect, insert_context: InsertContext
) -> None:
    context = InsertContext(
        target_schema=insert_context.target_schema,
        target_table=insert_context.target_table,
        columns=insert_context.columns,
        projection_cte=insert_context.projection_cte,
        primary_keys=insert_context.primary_keys,
        audit_table="migration_audit",
    )
    strategy = ConflictStrategyFactory.create(ConflictStrategy.IGNORE_AND_LOG.value, dialect)
    sql = strategy.build_insert_statement(context)

    assert "INSERT INTO core.migration_audit" in sql


def test_ignore_unprocessed_strategy_routes_to_unprocessed_table(
    dialect: MySqlDialect, insert_context: InsertContext
) -> None:
    context = InsertContext(
        target_schema=insert_context.target_schema,
        target_table=insert_context.target_table,
        columns=insert_context.columns,
        projection_cte=insert_context.projection_cte,
        primary_keys=insert_context.primary_keys,
        unprocessed_table="customers_unprocessed",
    )
    strategy = ConflictStrategyFactory.create(
        ConflictStrategy.IGNORE_AND_INSERT_UNPROCESSED.value,
        dialect,
    )
    sql = strategy.build_insert_statement(context)

    assert "INSERT INTO core.customers_unprocessed" in sql
    assert "INSERT IGNORE INTO core.customers" in sql


def test_ignore_unprocessed_requires_unprocessed_table(
    dialect: MySqlDialect, insert_context: InsertContext
) -> None:
    strategy = ConflictStrategyFactory.create(
        ConflictStrategy.IGNORE_AND_INSERT_UNPROCESSED.value,
        dialect,
    )

    with pytest.raises(ValueError, match="unprocessed_table"):
        strategy.build_insert_statement(insert_context)


def test_unknown_strategy_raises(dialect: MySqlDialect) -> None:
    with pytest.raises(ValueError, match="Unsupported conflict strategy"):
        ConflictStrategyFactory.create("REPLACE", dialect)
