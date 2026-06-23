"""CLI tests for validate command."""

import json
from pathlib import Path

from typer.testing import CliRunner

from migration_engine.__main__ import app

SAMPLE_CONFIG = Path(__file__).resolve().parents[3] / "docs" / "sampleConfigfile.json"


def _extract_report_json(stdout: str) -> dict:
    decoder = json.JSONDecoder()
    start = stdout.index("{")
    payload, _ = decoder.raw_decode(stdout, start)
    return payload


def test_validate_command_prints_summary_and_json() -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        ["validate", "--config", str(SAMPLE_CONFIG), "--dialect", "MYSQL"],
    )

    assert result.exit_code == 0, result.stdout
    assert "Validation passed" in result.stdout
    payload = _extract_report_json(result.stdout)
    assert payload["is_valid"] is True


def test_validate_command_writes_report_file(tmp_path: Path) -> None:
    runner = CliRunner()
    report_path = tmp_path / "validation.json"

    result = runner.invoke(
        app,
        [
            "validate",
            "--config",
            str(SAMPLE_CONFIG),
            "--report-file",
            str(report_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert report_path.is_file()
    assert "Validation report written" in result.stdout
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["is_valid"] is True
