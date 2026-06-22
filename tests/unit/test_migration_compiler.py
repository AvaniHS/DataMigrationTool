"""Unit tests for migration compiler."""

from pathlib import Path

import pytest

from migration_engine.compilers.migration_compiler import MigrationCompiler
from migration_engine.dialects.mysql_dialect import MySqlDialect
from migration_engine.parsers.blueprint_parser import BlueprintParser

SAMPLE_CONFIG = Path(__file__).resolve().parents[2] / "docs" / "sampleConfigfile.json"


def _normalize_sql(sql: str) -> str:
    return " ".join(sql.split())


@pytest.fixture
def migration():
    parser = BlueprintParser()
    return parser.parse_file(SAMPLE_CONFIG)


@pytest.fixture
def blueprint_one(migration):
    return migration.blueprints[0]


def test_compile_blueprint_one_produces_bootstrap_with_clause_and_upsert(
    migration, blueprint_one
) -> None:
    compiler = MigrationCompiler(MySqlDialect())
    sql = compiler.compile_blueprint(blueprint_one, migration.connections)

    assert "CREATE TEMPORARY TABLE _bootstrap_cm AS" in sql
    assert "CREATE TEMPORARY TABLE _bootstrap_gam AS" in sql
    assert sql.index("_bootstrap_cm") < sql.index("WITH")
    assert "WITH" in sql
    assert "bp1_target_projection AS (" in sql
    assert "INSERT INTO core.customers (id, company_name, phone, country_iso)" in sql
    assert "ON DUPLICATE KEY UPDATE" in sql
    assert sql.endswith(";")


def test_compile_blueprint_insert_only_reads_projection_cte(migration, blueprint_one) -> None:
    compiler = MigrationCompiler(MySqlDialect())
    sql = compiler.compile_blueprint(blueprint_one, migration.connections)
    insert_part = sql.split("INSERT INTO", maxsplit=1)[1]

    assert "JOIN" not in insert_part
    assert "WHERE" not in insert_part
    assert "REGEXP_REPLACE" not in insert_part


def test_compile_blueprint_two_is_runnable_structure(migration) -> None:
    compiler = MigrationCompiler(MySqlDialect())
    blueprint = migration.blueprints[1]
    sql = compiler.compile_blueprint(blueprint, migration.connections)

    assert "CREATE TEMPORARY TABLE _bootstrap_tih AS" in sql
    assert "CREATE TEMPORARY TABLE _bootstrap_til AS" in sql
    assert "CREATE TEMPORARY TABLE _bootstrap_st AS" in sql
    assert "bp2_target_projection AS (" in sql
    assert "INSERT INTO billing.billing_details" in sql


def test_compile_blueprint_matches_golden_fragment(migration, blueprint_one) -> None:
    compiler = MigrationCompiler(MySqlDialect())
    sql = compiler.compile_blueprint(blueprint_one, migration.connections)
    golden_path = (
        Path(__file__).resolve().parents[1]
        / "golden"
        / "expected"
        / "bp1_cte_pipeline.sql"
    )
    expected = golden_path.read_text(encoding="utf-8")

    assert _normalize_sql(sql) == _normalize_sql(expected)
