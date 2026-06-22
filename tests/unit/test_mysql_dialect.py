"""Unit tests for MySqlDialect."""

import pytest

from migration_engine.dialects.mysql_dialect import MySqlDialect


@pytest.fixture
def dialect() -> MySqlDialect:
    return MySqlDialect()


def test_dialect_type(dialect: MySqlDialect) -> None:
    assert dialect.dialect_type == "MYSQL"


def test_qualify_table(dialect: MySqlDialect) -> None:
    assert dialect.qualify_table("core", "customers") == "core.customers"


def test_safe_cast_varchar(dialect: MySqlDialect) -> None:
    result = dialect.safe_cast("cm.name", "VARCHAR(255)")
    assert "NULLIF(TRIM(CAST(cm.name AS CHAR)), '')" == result


def test_safe_cast_uuid(dialect: MySqlDialect) -> None:
    result = dialect.safe_cast("cm.global_uuid", "UUID")
    assert "REGEXP" in result
    assert "cm.global_uuid" in result


def test_safe_cast_decimal(dialect: MySqlDialect) -> None:
    result = dialect.safe_cast("til.unit_price", "DECIMAL(12,4)")
    assert "CAST(til.unit_price AS DECIMAL(12,4))" in result
    assert "REGEXP" in result


def test_safe_cast_date(dialect: MySqlDialect) -> None:
    result = dialect.safe_cast("tih.invoice_date", "DATE")
    assert "STR_TO_DATE(tih.invoice_date, '%Y-%m-%d')" in result


def test_safe_cast_fallback(dialect: MySqlDialect) -> None:
    result = dialect.safe_cast("payload", "JSON")
    assert result == "CAST(payload AS JSON)"


def test_concat_multiple_expressions(dialect: MySqlDialect) -> None:
    result = dialect.concat("'WEB'", "tih.invoice_number")
    assert result == "CONCAT('WEB', tih.invoice_number)"


def test_concat_single_expression(dialect: MySqlDialect) -> None:
    assert dialect.concat("tih.invoice_number") == "tih.invoice_number"


def test_concat_requires_expression(dialect: MySqlDialect) -> None:
    with pytest.raises(ValueError, match="at least one expression"):
        dialect.concat()


def test_regexp_replace(dialect: MySqlDialect) -> None:
    result = dialect.regexp_replace("cm.phone_raw", "[^0-9+]", "")
    assert result == "REGEXP_REPLACE(cm.phone_raw, '[^0-9+]', '')"


def test_on_duplicate_key_update(dialect: MySqlDialect) -> None:
    result = dialect.on_duplicate_key_update(
        ["id", "company_name", "phone"],
        ["id"],
    )
    assert result == (
        "ON DUPLICATE KEY UPDATE company_name = VALUES(company_name), "
        "phone = VALUES(phone)"
    )


def test_on_duplicate_key_update_no_non_pk_columns(dialect: MySqlDialect) -> None:
    result = dialect.on_duplicate_key_update(["id"], ["id"])
    assert result == "ON DUPLICATE KEY UPDATE id = id"


def test_primary_key_join(dialect: MySqlDialect) -> None:
    result = dialect.primary_key_join("p", "t", ["tenant_id", "invoice_no"])
    assert result == "p.tenant_id = t.tenant_id AND p.invoice_no = t.invoice_no"


def test_transaction_statements(dialect: MySqlDialect) -> None:
    assert dialect.begin_transaction() == "START TRANSACTION;"
    assert dialect.savepoint("bp_step_1") == "SAVEPOINT bp_step_1;"
    assert dialect.release_savepoint("bp_step_1") == "RELEASE SAVEPOINT bp_step_1;"
    assert dialect.rollback_to_savepoint("bp_step_1") == "ROLLBACK TO SAVEPOINT bp_step_1;"
    assert dialect.commit() == "COMMIT;"
