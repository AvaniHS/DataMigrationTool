"""Unit tests for validation report formatting and export."""

import json
from pathlib import Path

from migration_engine.parsers.blueprint_parser import BlueprintParser
from migration_engine.validators.migration_config_validator import MigrationConfigValidator
from migration_engine.validators.report_writer import write_validation_report
from migration_engine.validators.validation_result import ValidationIssue, ValidationReport

SAMPLE_CONFIG = Path(__file__).resolve().parents[2] / "docs" / "sampleConfigfile.json"


def test_format_summary_for_valid_report() -> None:
    report = ValidationReport(migration_id="mig_ok", is_valid=True)

    assert "Validation passed" in report.format_summary()


def test_format_summary_lists_issues_with_codes() -> None:
    report = ValidationReport(migration_id="mig_bad", is_valid=True)
    report.add_issue(
        "UNKNOWN_CONNECTION_REF",
        "Connection 'missing' is not defined.",
        path="blueprints[0].target.connection_ref",
        blueprint_sequence=1,
    )

    summary = report.format_summary()

    assert "Validation failed" in summary
    assert "[UNKNOWN_CONNECTION_REF]" in summary
    assert "blueprint 1" in summary


def test_write_validation_report_creates_json_file(tmp_path: Path) -> None:
    migration = BlueprintParser().parse_file(SAMPLE_CONFIG)
    report = MigrationConfigValidator().validate(migration)
    report_path = tmp_path / "reports" / "validation.json"

    written = write_validation_report(report, report_path)

    assert written.is_file()
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload["migration_id"] == migration.migration_id
    assert payload["is_valid"] is True


def test_validation_issue_round_trips_through_to_dict() -> None:
    issue = ValidationIssue(
        code="TEST",
        message="Example",
        path="blueprints[0]",
        blueprint_sequence=1,
    )
    report = ValidationReport(migration_id="mig", is_valid=False, issues=[issue])

    assert report.to_dict()["issues"][0]["code"] == "TEST"
