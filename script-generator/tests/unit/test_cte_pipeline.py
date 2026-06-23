"""Unit tests for CTE pipeline builder."""

import json
from pathlib import Path

import pytest

from migration_engine.compilers.cte_pipeline_builder import CtePipelineBuilder
from migration_engine.dialects.mysql_dialect import MySqlDialect
from migration_engine.parsers.blueprint_parser import BlueprintParser

SAMPLE_CONFIG = Path(__file__).resolve().parents[3] / "docs" / "sampleConfigfile.json"


@pytest.fixture
def dialect() -> MySqlDialect:
    return MySqlDialect()


@pytest.fixture
def blueprint_one():
    parser = BlueprintParser()
    migration = parser.parse_file(SAMPLE_CONFIG)
    return migration.blueprints[0]


@pytest.fixture
def migration():
    return BlueprintParser().parse_file(SAMPLE_CONFIG)


@pytest.fixture
def pipeline_builder() -> CtePipelineBuilder:
    return CtePipelineBuilder()


def test_pipeline_stage_names_for_blueprint_one(
    pipeline_builder: CtePipelineBuilder,
    dialect: MySqlDialect,
    blueprint_one,
) -> None:
    pipeline = pipeline_builder.build(blueprint_one, dialect)
    stage_names = [stage.name for stage in pipeline.stages]

    assert stage_names == [
        "bp1_stg_cm",
        "bp1_stg_gam",
        "bp1_pre_filtered_cm",
        "bp1_joined_cm",
        "bp1_calculation_layer",
        "bp1_target_projection",
    ]


def test_source_stage_reads_bootstrap_table(
    pipeline_builder: CtePipelineBuilder,
    dialect: MySqlDialect,
    blueprint_one,
) -> None:
    pipeline = pipeline_builder.build(blueprint_one, dialect)
    root_stage = pipeline.stages[0]

    assert root_stage.name == "bp1_stg_cm"
    assert "FROM _bootstrap_cm" in root_stage.body


def test_pre_filter_stage_applies_predicates(
    pipeline_builder: CtePipelineBuilder,
    dialect: MySqlDialect,
    blueprint_one,
) -> None:
    pipeline = pipeline_builder.build(blueprint_one, dialect)
    pre_filter_stage = next(
        stage for stage in pipeline.stages if stage.name == "bp1_pre_filtered_cm"
    )

    assert "WHERE cm.status = 'ACTIVE'" in pre_filter_stage.body
    assert "FROM bp1_stg_cm AS cm" in pre_filter_stage.body


def test_join_stage_builds_left_join(
    pipeline_builder: CtePipelineBuilder,
    dialect: MySqlDialect,
    blueprint_one,
) -> None:
    pipeline = pipeline_builder.build(blueprint_one, dialect)
    join_stage = next(stage for stage in pipeline.stages if stage.name == "bp1_joined_cm")

    assert "SELECT cm.*, gam.*" in join_stage.body
    assert "LEFT JOIN bp1_stg_gam AS gam" in join_stage.body
    assert "ON gam.legacy_cust_id = cm.id" in join_stage.body


def test_derivation_stage_preserves_source_aliases(
    pipeline_builder: CtePipelineBuilder,
    dialect: MySqlDialect,
    blueprint_one,
) -> None:
    pipeline = pipeline_builder.build(blueprint_one, dialect)
    derivation_stage = next(
        stage for stage in pipeline.stages if stage.name == "bp1_calculation_layer"
    )

    assert "REGEXP_REPLACE(cm.phone_raw, '[^0-9+]', '') AS formatted_phone" in derivation_stage.body
    assert "FROM bp1_pre_filtered_cm AS cm" in derivation_stage.body
    assert "LEFT JOIN bp1_stg_gam AS gam" in derivation_stage.body


def test_projection_stage_applies_safe_cast_and_derived_mapping(
    pipeline_builder: CtePipelineBuilder,
    dialect: MySqlDialect,
    blueprint_one,
) -> None:
    pipeline = pipeline_builder.build(blueprint_one, dialect)
    projection_stage = next(
        stage for stage in pipeline.stages if stage.name == "bp1_target_projection"
    )

    assert "AS id" in projection_stage.body
    assert "AS company_name" in projection_stage.body
    assert "formatted_phone" in projection_stage.body
    assert "COALESCE(gam.country_code, 'USA')" in projection_stage.body
    assert "FROM bp1_calculation_layer" in projection_stage.body


def test_post_filter_stage_is_inserted_when_configured(
    pipeline_builder: CtePipelineBuilder,
    dialect: MySqlDialect,
) -> None:
    payload = json.loads(SAMPLE_CONFIG.read_text(encoding="utf-8"))
    payload["blueprints"][0]["post_filters"] = ["formatted_phone IS NOT NULL"]
    migration = BlueprintParser().parse_text(json.dumps(payload))
    blueprint = migration.blueprints[0]

    pipeline = pipeline_builder.build(blueprint, dialect)
    stage_names = [stage.name for stage in pipeline.stages]

    assert "bp1_filtered_results" in stage_names
    filtered_stage = next(
        stage for stage in pipeline.stages if stage.name == "bp1_filtered_results"
    )
    assert "WHERE formatted_phone IS NOT NULL" in filtered_stage.body

    projection_stage = next(
        stage for stage in pipeline.stages if stage.name == "bp1_target_projection"
    )
    assert "FROM bp1_filtered_results" in projection_stage.body


def test_render_with_clause_contains_all_stage_names(
    pipeline_builder: CtePipelineBuilder,
    dialect: MySqlDialect,
    blueprint_one,
) -> None:
    pipeline = pipeline_builder.build(blueprint_one, dialect)
    sql = pipeline.render_with_clause()

    assert sql.startswith("WITH")
    assert "bp1_stg_cm AS (" in sql
    assert "bp1_target_projection AS (" in sql


def test_chunk_filter_stage_inserted_for_chunked_blueprint(
    pipeline_builder: CtePipelineBuilder,
    dialect: MySqlDialect,
    migration,
) -> None:
    blueprint = migration.blueprints[1]
    pipeline = pipeline_builder.build(blueprint, dialect, use_chunk_filter=True)
    stage_names = [stage.name for stage in pipeline.stages]

    assert "bp2_chunk_filtered" in stage_names
    chunk_stage = next(stage for stage in pipeline.stages if stage.name == "bp2_chunk_filtered")
    assert "tih.id > @bp2_chunk_min" in chunk_stage.body
    assert "FROM bp2_stg_tih AS tih" in chunk_stage.body

    pre_filter_stage = next(
        stage for stage in pipeline.stages if stage.name == "bp2_pre_filtered_tih"
    )
    assert "FROM bp2_chunk_filtered AS tih" in pre_filter_stage.body
