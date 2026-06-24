"""Migration engine CLI."""

import json
import sys
from pathlib import Path

import typer

from migration_engine.factories.script_generator_factory import ScriptGeneratorFactory
from migration_engine.generators.errors import ScriptGenerationError
from migration_engine.logging.structured_logger import get_logger
from migration_engine.models import MasterMigrationBlueprint
from migration_engine.models.enums import DialectType
from migration_engine.parsers.blueprint_parser import BlueprintParseError, BlueprintParser
from migration_engine.validators.report_writer import write_validation_report
from migration_engine.validators.validation_result import ValidationIssue, ValidationReport
from migration_engine.validation_service import validate_migration_payload

app = typer.Typer(
    name="migration-engine",
    help="Configuration-driven ELT migration SQL generator.",
    no_args_is_help=True,
)

logger = get_logger(__name__)

EXIT_SUCCESS = 0
EXIT_VALIDATION_FAILURE = 1
EXIT_PARSE_FAILURE = 2
EXIT_COMPILATION_FAILURE = 2


def _report_from_dict(report_dict: dict) -> ValidationReport:
    report = ValidationReport(
        migration_id=str(report_dict.get("migration_id", "unknown")),
        is_valid=bool(report_dict.get("is_valid", False)),
    )
    for issue in report_dict.get("issues", []):
        report.issues.append(
            ValidationIssue(
                code=str(issue.get("code", "VALIDATION_ERROR")),
                message=str(issue.get("message", "")),
                path=str(issue.get("path", "")),
                blueprint_sequence=issue.get("blueprint_sequence"),
            )
        )
    if report.issues:
        report.is_valid = False
    return report


def _resolve_config_path(config: Path) -> Path:
    return config.expanduser().resolve()


def _resolve_output_path(output: Path) -> Path:
    return output.expanduser().resolve()


def _parse_dialect(dialect: str) -> DialectType:
    try:
        return DialectType(dialect.upper())
    except ValueError as exc:
        typer.echo(f"Unsupported dialect: {dialect}", err=True)
        raise typer.Exit(EXIT_VALIDATION_FAILURE) from exc


def _load_migration_config(config_path: Path) -> MasterMigrationBlueprint:
    parser = BlueprintParser()
    try:
        return parser.parse_file(config_path)
    except BlueprintParseError as exc:
        logger.error("parse_failed", error=str(exc), config=str(config_path))
        typer.echo(f"Parse error: {exc}", err=True)
        if exc.details:
            typer.echo(json.dumps({"parse_errors": exc.details}, indent=2), err=True)
        raise typer.Exit(EXIT_PARSE_FAILURE) from exc


@app.command("validate")
def validate_command(
    config: Path = typer.Option(..., "--config", "-c", help="Path to migration JSON file."),
    dialect: str = typer.Option(
        DialectType.MYSQL.value,
        "--dialect",
        "-d",
        help="Target SQL dialect used for connectivity rules.",
    ),
    report_file: Path | None = typer.Option(
        None,
        "--report-file",
        "-r",
        help="Optional path to write the validation report as JSON.",
    ),
) -> None:
    """Validate a migration blueprint configuration file."""
    config_path = _resolve_config_path(config)
    dialect_type = _parse_dialect(dialect)
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("parse_failed", error=str(exc), config=str(config_path))
        typer.echo(f"Parse error: {exc}", err=True)
        raise typer.Exit(EXIT_PARSE_FAILURE) from exc

    report_dict = validate_migration_payload(payload, dialect=dialect_type)
    report = _report_from_dict(report_dict)

    typer.echo(report.format_summary())
    typer.echo(json.dumps(report.to_dict(), indent=2))

    if report_file is not None:
        written = write_validation_report(report, report_file)
        typer.echo(f"Validation report written: {written}")

    if report.is_valid:
        logger.info(
            "validation_succeeded",
            migration_id=report.migration_id,
        )
        raise typer.Exit(EXIT_SUCCESS)

    logger.warning(
        "validation_failed",
        migration_id=report.migration_id,
        issue_count=len(report.issues),
    )
    raise typer.Exit(EXIT_VALIDATION_FAILURE)


@app.command("generate")
def generate_command(
    config: Path = typer.Option(..., "--config", "-c", help="Path to migration JSON file."),
    output: Path = typer.Option(..., "--output", "-o", help="Output SQL file path."),
    dialect: str = typer.Option(
        DialectType.MYSQL.value,
        "--dialect",
        "-d",
        help="Target SQL dialect for script generation.",
    ),
) -> None:
    """Generate a migration SQL script from a validated blueprint."""
    config_path = _resolve_config_path(config)
    output_path = _resolve_output_path(output)
    migration = _load_migration_config(config_path)
    dialect_type = _parse_dialect(dialect)

    generator = ScriptGeneratorFactory.create(
        migration.output_format.value,
        dialect_type=dialect_type.value,
    )

    try:
        script = generator.generate(migration)
    except ScriptGenerationError as exc:
        logger.error(
            "generation_failed",
            migration_id=migration.migration_id,
            error=str(exc),
        )
        typer.echo(f"Generation error: {exc}", err=True)
        if exc.validation_report is not None:
            typer.echo(exc.validation_report.format_summary(), err=True)
            typer.echo(json.dumps(exc.validation_report.to_dict(), indent=2), err=True)
        raise typer.Exit(EXIT_COMPILATION_FAILURE) from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(script.content, encoding="utf-8")

    logger.info(
        "generation_succeeded",
        migration_id=script.migration_id,
        output_format=script.output_format,
        output=str(output_path),
    )
    typer.echo(f"Generated SQL script: {output_path}")
    raise typer.Exit(EXIT_SUCCESS)


def main() -> None:
    try:
        app()
    except typer.Exit as exc:
        sys.exit(exc.exit_code)


if __name__ == "__main__":
    main()
