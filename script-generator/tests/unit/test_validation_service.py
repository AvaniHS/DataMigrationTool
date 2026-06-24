"""Tests for shared validation service."""

import json
from pathlib import Path

from migration_engine.validation_service import validate_migration_payload

SAMPLE_CONFIG = Path(__file__).resolve().parents[3] / "docs" / "sampleConfigfile.json"


def test_validate_sample_config_passes() -> None:
    payload = json.loads(SAMPLE_CONFIG.read_text(encoding="utf-8"))
    report = validate_migration_payload(payload)
    assert report["is_valid"] is True
    assert report["issue_count"] == 0


def test_validate_invalid_payload_reports_parse_issue() -> None:
    report = validate_migration_payload({"migration_id": "broken"})
    assert report["is_valid"] is False
    assert report["issues"]
    assert report["issues"][0]["code"] == "PARSE_ERROR"
