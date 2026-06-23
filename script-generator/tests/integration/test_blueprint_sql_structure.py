"""Integration-style tests for runnable blueprint SQL structure."""

import pytest


@pytest.mark.integration
def test_sample_config_validates_before_compilation(validation_report) -> None:
    assert validation_report.is_valid is True


@pytest.mark.integration
@pytest.mark.parametrize("blueprint_index", [0, 1])
def test_blueprint_generates_self_contained_script(migration, compiler, blueprint_index: int) -> None:
    blueprint = migration.blueprints[blueprint_index]
    sql = compiler.compile_blueprint(blueprint, migration.connections)

    assert "CREATE TEMPORARY TABLE _bootstrap_" in sql
    assert "START TRANSACTION;" in sql
    assert "WITH" in sql
    assert "INSERT INTO" in sql
    assert f"bp{blueprint.sequence_order}_target_projection" in sql
    assert "COMMIT;" in sql


@pytest.mark.integration
def test_full_migration_generates_three_transaction_blocks(migration, compiler) -> None:
    sql = compiler.compile_migration(migration)

    assert sql.count("START TRANSACTION;") == 3
    assert sql.count("COMMIT;") == 3
    assert "WHILE @bp2_chunk_min <= @bp2_chunk_max DO" in sql
