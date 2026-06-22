"""Migration engine CLI."""

import json
import sys
from pathlib import Path

import typer

from migration_engine.logging.structured_logger import get_logger
from migration_engine.models.enums import DialectType
from migration_engine.parsers.blueprint_parser import BlueprintParseError, BlueprintParser
from migration_engine.validators.migration_config_validator import MigrationConfigValidator

app = typer.Typer(
    name="migration-engine",
    help="Configuration-driven ELT migration SQL generator.",
    no_args_is_help=True,
)

logger = get_logger(__name__)

EXIT_SUCCESS = 0
EXIT_VALIDATION_FAILURE = 1
EXIT_PARSE_FAILURE = 2


def _resolve_config_path(config: Path) -> Path:
    return config.expanduser().resolve()


@app.command("validate")
def validate_command(
    config: Path = typer.Option(..., "--config", "-c", help="Path to migration JSON file."),
    dialect: str = typer.Option(
        DialectType.MYSQL.value,
        "--dialect",
        "-d",
        help="Target SQL dialect used for connectivity rules.",
    ),
) -> None:
    """Validate a migration blueprint configuration file."""
    config_path = _resolve_config_path(config)
    parser = BlueprintParser()

    try:
        blueprint = parser.parse_file(config_path)
    except BlueprintParseError as exc:
        logger.error("parse_failed", error=str(exc), config=str(config_path))
        typer.echo(f"Parse error: {exc}", err=True)
        raise typer.Exit(EXIT_PARSE_FAILURE) from exc

    try:
        dialect_type = DialectType(dialect.upper())
    except ValueError as exc:
        typer.echo(f"Unsupported dialect: {dialect}", err=True)
        raise typer.Exit(EXIT_VALIDATION_FAILURE) from exc

    validator = MigrationConfigValidator(compile_dialect=dialect_type)
    report = validator.validate(blueprint)

    typer.echo(json.dumps(report.to_dict(), indent=2))

    if report.is_valid:
        logger.info(
            "validation_succeeded",
            migration_id=blueprint.migration_id,
            blueprint_count=len(blueprint.blueprints),
        )
        raise typer.Exit(EXIT_SUCCESS)

    logger.warning(
        "validation_failed",
        migration_id=blueprint.migration_id,
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
    typer.echo("SQL generation is implemented in Phase 6.", err=True)
    raise typer.Exit(2)


def main() -> None:
    try:
        app()
    except typer.Exit as exc:
        sys.exit(exc.exit_code)


if __name__ == "__main__":
    main()
