"""Integration-style tests for runnable blueprint SQL structure."""

from pathlib import Path

import pytest

from migration_engine.compilers.migration_compiler import MigrationCompiler
from migration_engine.dialects.mysql_dialect import MySqlDialect
from migration_engine.parsers.blueprint_parser import BlueprintParser
from migration_engine.validators.migration_config_validator import MigrationConfigValidator

SAMPLE_CONFIG = Path(__file__).resolve().parents[2] / "docs" / "sampleConfigfile.json"


@pytest.fixture
def migration():
    return BlueprintParser().parse_file(SAMPLE_CONFIG)


def test_sample_config_validates_before_compilation(migration) -> None:
    report = MigrationConfigValidator().validate(migration)
    assert report.is_valid is True


@pytest.mark.parametrize("blueprint_index", [0, 1])
def test_blueprint_generates_self_contained_script(migration, blueprint_index: int) -> None:
    compiler = MigrationCompiler(MySqlDialect())
    blueprint = migration.blueprints[blueprint_index]
    sql = compiler.compile_blueprint(blueprint, migration.connections)

    assert "CREATE TEMPORARY TABLE _bootstrap_" in sql
    assert "START TRANSACTION;" in sql
    assert "WITH" in sql
    assert "INSERT INTO" in sql
    assert f"bp{blueprint.sequence_order}_target_projection" in sql
    assert "COMMIT;" in sql


def test_full_migration_generates_three_transaction_blocks(migration) -> None:
    compiler = MigrationCompiler(MySqlDialect())
    sql = compiler.compile_migration(migration)

    assert sql.count("START TRANSACTION;") == 3
    assert sql.count("COMMIT;") == 3
    assert "WHILE @bp2_chunk_min <= @bp2_chunk_max DO" in sql
