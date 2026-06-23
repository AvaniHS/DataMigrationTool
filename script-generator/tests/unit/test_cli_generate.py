"""CLI tests for generate command."""

from pathlib import Path

from typer.testing import CliRunner

from migration_engine.__main__ import app

SAMPLE_CONFIG = Path(__file__).resolve().parents[3] / "docs" / "sampleConfigfile.json"


def test_generate_command_writes_sql_file(tmp_path: Path) -> None:
    runner = CliRunner()
    output_path = tmp_path / "migration.sql"

    result = runner.invoke(
        app,
        [
            "generate",
            "--config",
            str(SAMPLE_CONFIG),
            "--output",
            str(output_path),
            "--dialect",
            "MYSQL",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert output_path.is_file()
    assert "START TRANSACTION;" in output_path.read_text(encoding="utf-8")
    assert "Migration: mig_multi_server_enterprise_2026" in output_path.read_text(encoding="utf-8")


def test_generate_command_fails_for_missing_config(tmp_path: Path) -> None:
    runner = CliRunner()
    output_path = tmp_path / "migration.sql"

    result = runner.invoke(
        app,
        [
            "generate",
            "--config",
            str(tmp_path / "missing.json"),
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 2
    assert not output_path.exists()
