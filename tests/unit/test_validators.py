"""Unit tests for migration config validators."""

import json
from pathlib import Path

import pytest

from migration_engine.parsers.blueprint_parser import BlueprintParser
from migration_engine.validators.migration_config_validator import MigrationConfigValidator

SAMPLE_CONFIG = Path(__file__).resolve().parents[2] / "docs" / "sampleConfigfile.json"


@pytest.fixture
def sample_blueprint():
    parser = BlueprintParser()
    return parser.parse_file(SAMPLE_CONFIG)


def test_sample_config_validates_successfully(sample_blueprint) -> None:
    validator = MigrationConfigValidator()
    report = validator.validate(sample_blueprint)

    assert report.is_valid is True
    assert report.issues == []


def test_unknown_connection_ref_fails(sample_blueprint) -> None:
    payload = json.loads(SAMPLE_CONFIG.read_text(encoding="utf-8"))
    payload["blueprints"][0]["target"]["connection_ref"] = "missing_connection"
    blueprint = BlueprintParser().parse_text(json.dumps(payload))

    report = MigrationConfigValidator().validate(blueprint)

    assert report.is_valid is False
    assert any(issue.code == "UNKNOWN_CONNECTION_REF" for issue in report.issues)


def test_duplicate_sequence_order_fails(sample_blueprint) -> None:
    payload = json.loads(SAMPLE_CONFIG.read_text(encoding="utf-8"))
    payload["blueprints"][1]["sequence_order"] = 1
    blueprint = BlueprintParser().parse_text(json.dumps(payload))

    report = MigrationConfigValidator().validate(blueprint)

    assert report.is_valid is False
    assert any(issue.code == "DUPLICATE_SEQUENCE_ORDER" for issue in report.issues)


def test_disallowed_function_fails(sample_blueprint) -> None:
    payload = json.loads(SAMPLE_CONFIG.read_text(encoding="utf-8"))
    payload["blueprints"][0]["derivations"][0]["expression"] = "UNSUPPORTED_FUNC(cm.phone_raw)"
    blueprint = BlueprintParser().parse_text(json.dumps(payload))

    report = MigrationConfigValidator().validate(blueprint)

    assert report.is_valid is False
    assert any(issue.code == "DISALLOWED_FUNCTION" for issue in report.issues)


def test_unknown_derivation_reference_fails(sample_blueprint) -> None:
    payload = json.loads(SAMPLE_CONFIG.read_text(encoding="utf-8"))
    payload["blueprints"][0]["mappings"][2]["source_value"] = "derivations.missing_var"
    blueprint = BlueprintParser().parse_text(json.dumps(payload))

    report = MigrationConfigValidator().validate(blueprint)

    assert report.is_valid is False
    assert any(issue.code == "UNKNOWN_DERIVATION" for issue in report.issues)


def test_chunking_requires_chunk_fields() -> None:
    payload = json.loads(SAMPLE_CONFIG.read_text(encoding="utf-8"))
    payload["blueprints"][1]["chunking_strategy"] = {
        "is_enabled": True,
        "chunk_by_column": None,
        "chunk_size": None,
    }
    blueprint = BlueprintParser().parse_text(json.dumps(payload))

    report = MigrationConfigValidator().validate(blueprint)

    assert report.is_valid is False
    assert any(issue.code == "CHUNK_COLUMN_REQUIRED" for issue in report.issues)
