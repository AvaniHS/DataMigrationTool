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
def blueprint_one():
    parser = BlueprintParser()
    migration = parser.parse_file(SAMPLE_CONFIG)
    return migration.blueprints[0]


def test_compile_blueprint_one_produces_with_insert_and_upsert(blueprint_one) -> None:
    compiler = MigrationCompiler(MySqlDialect())
    sql = compiler.compile_blueprint(blueprint_one)

    assert sql.startswith("WITH")
    assert "bp1_target_projection AS (" in sql
    assert "INSERT INTO core.customers (id, company_name, phone, country_iso)" in sql
    assert "FROM bp1_target_projection" in sql
    assert "ON DUPLICATE KEY UPDATE" in sql
    assert sql.endswith(";")


def test_compile_blueprint_insert_only_reads_projection_cte(blueprint_one) -> None:
    compiler = MigrationCompiler(MySqlDialect())
    sql = compiler.compile_blueprint(blueprint_one)
    insert_part = sql.split("INSERT INTO", maxsplit=1)[1]

    assert "JOIN" not in insert_part
    assert "WHERE" not in insert_part
    assert "REGEXP_REPLACE" not in insert_part


def test_compile_blueprint_matches_golden_fragment(blueprint_one) -> None:
    compiler = MigrationCompiler(MySqlDialect())
    sql = compiler.compile_blueprint(blueprint_one)
    golden_path = (
        Path(__file__).resolve().parents[1]
        / "golden"
        / "expected"
        / "bp1_cte_pipeline.sql"
    )
    expected = golden_path.read_text(encoding="utf-8")

    assert _normalize_sql(sql) == _normalize_sql(expected)
