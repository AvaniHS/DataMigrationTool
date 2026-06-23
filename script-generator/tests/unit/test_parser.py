"""Unit tests for blueprint parser."""

import json
from pathlib import Path

import pytest

from migration_engine.models.enums import ConflictStrategy, OutputFormat, SourceType
from migration_engine.parsers.blueprint_parser import BlueprintParseError, BlueprintParser

SAMPLE_CONFIG = Path(__file__).resolve().parents[3] / "docs" / "sampleConfigfile.json"


def test_parse_sample_config_file() -> None:
    parser = BlueprintParser()
    blueprint = parser.parse_file(SAMPLE_CONFIG)

    assert blueprint.migration_id == "mig_multi_server_enterprise_2026"
    assert blueprint.client_id == "client_global_retail_corp"
    assert blueprint.output_format == OutputFormat.SQL
    assert len(blueprint.connections) == 5
    assert len(blueprint.blueprints) == 3


def test_parse_strips_json_schema_field() -> None:
    parser = BlueprintParser()
    payload = json.loads(SAMPLE_CONFIG.read_text(encoding="utf-8"))
    payload["$schema"] = "https://example.com/schema"
    blueprint = parser.parse_text(json.dumps(payload))

    assert blueprint.migration_id == "mig_multi_server_enterprise_2026"


def test_parse_invalid_json_raises() -> None:
    parser = BlueprintParser()
    with pytest.raises(BlueprintParseError, match="Invalid JSON"):
        parser.parse_text("{not-json")


def test_parse_missing_required_field_raises() -> None:
    parser = BlueprintParser()
    payload = {"migration_id": "only-id"}
    with pytest.raises(BlueprintParseError, match="schema validation failed"):
        parser.parse_text(json.dumps(payload))


def test_blueprint_target_and_mapping_types() -> None:
    parser = BlueprintParser()
    blueprint = parser.parse_file(SAMPLE_CONFIG)
    first = blueprint.blueprints[0]

    assert first.target.on_conflict == ConflictStrategy.UPSERT
    assert first.mappings[2].source_type == SourceType.DERIVED
    assert first.mappings[2].source_value == "derivations.formatted_phone"
