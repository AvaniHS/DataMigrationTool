"""Unit tests for chunking procedural builder."""

from migration_engine.compilers.chunking_procedural_builder import ChunkingProceduralBuilder
from migration_engine.dialects.mysql_dialect import MySqlDialect
from migration_engine.parsers.blueprint_parser import BlueprintParser
from pathlib import Path

SAMPLE_CONFIG = Path(__file__).resolve().parents[3] / "docs" / "sampleConfigfile.json"


def test_chunk_setup_statements_for_blueprint_two() -> None:
    migration = BlueprintParser().parse_file(SAMPLE_CONFIG)
    blueprint = migration.blueprints[1]
    builder = ChunkingProceduralBuilder(MySqlDialect())

    setup = builder.build_setup_statements(blueprint)

    assert "@bp2_chunk_min = 0" in setup
    assert "@bp2_chunk_size = 25000" in setup
    assert "@bp2_chunk_max" in setup
    assert "tih.id" in setup


def test_wrap_in_chunk_loop_adds_while_and_chunk_savepoint() -> None:
    migration = BlueprintParser().parse_file(SAMPLE_CONFIG)
    blueprint = migration.blueprints[1]
    builder = ChunkingProceduralBuilder(MySqlDialect())

    wrapped = builder.wrap_in_chunk_loop(blueprint, "WITH bp2_stg_tih AS (SELECT 1) INSERT INTO t SELECT 1")

    assert wrapped.startswith("WHILE @bp2_chunk_min <= @bp2_chunk_max DO")
    assert "SAVEPOINT bp_step_2_chunk;" in wrapped
    assert "RELEASE SAVEPOINT bp_step_2_chunk;" in wrapped
    assert wrapped.endswith("END WHILE;")


def test_wrap_in_chunk_loop_passthrough_when_disabled() -> None:
    migration = BlueprintParser().parse_file(SAMPLE_CONFIG)
    blueprint = migration.blueprints[0]
    builder = ChunkingProceduralBuilder(MySqlDialect())

    inner = "WITH bp1_stg_cm AS (SELECT 1) INSERT INTO t SELECT 1;"
    assert builder.wrap_in_chunk_loop(blueprint, inner) == inner
