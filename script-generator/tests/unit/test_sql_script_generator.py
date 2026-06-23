"""Unit tests for SQL script generator."""

from pathlib import Path

import pytest

from migration_engine.factories.script_generator_factory import ScriptGeneratorFactory
from migration_engine.generators.errors import ScriptGenerationError
from migration_engine.generators.sql_script_generator import SqlScriptGenerator
from migration_engine.models.enums import DialectType, OutputFormat
from migration_engine.parsers.blueprint_parser import BlueprintParser

SAMPLE_CONFIG = Path(__file__).resolve().parents[3] / "docs" / "sampleConfigfile.json"
GOLDEN_MIGRATION = (
    Path(__file__).resolve().parents[1] / "golden" / "expected" / "sample_migration.sql"
)


def _normalize_sql(sql: str) -> str:
    return " ".join(sql.split())


@pytest.fixture
def migration():
    return BlueprintParser().parse_file(SAMPLE_CONFIG)


def test_factory_creates_sql_generator_with_dialect() -> None:
    generator = ScriptGeneratorFactory.create(
        OutputFormat.SQL.value,
        dialect_type=DialectType.MYSQL.value,
    )
    assert isinstance(generator, SqlScriptGenerator)


def test_generate_returns_script_matching_golden_migration(migration) -> None:
    generator = SqlScriptGenerator(dialect_type=DialectType.MYSQL.value)
    script = generator.generate(migration)

    assert script.migration_id == "mig_multi_server_enterprise_2026"
    assert script.output_format == OutputFormat.SQL.value
    expected = GOLDEN_MIGRATION.read_text(encoding="utf-8")
    assert _normalize_sql(script.content) == _normalize_sql(expected)


def test_generate_raises_when_config_invalid(migration) -> None:
    generator = SqlScriptGenerator(dialect_type=DialectType.MYSQL.value)
    invalid = migration.model_copy(
        update={"blueprints": ()},
    )

    with pytest.raises(ScriptGenerationError, match="Validation failed"):
        generator.generate(invalid)
