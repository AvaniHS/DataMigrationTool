"""Shared fixtures for integration-style SQL tests."""

from pathlib import Path

import pytest

from migration_engine.compilers.migration_compiler import MigrationCompiler
from migration_engine.dialects.mysql_dialect import MySqlDialect
from migration_engine.generators.sql_script_generator import SqlScriptGenerator
from migration_engine.parsers.blueprint_parser import BlueprintParser
from migration_engine.validators.migration_config_validator import MigrationConfigValidator

SAMPLE_CONFIG = Path(__file__).resolve().parents[3] / "docs" / "sampleConfigfile.json"
GOLDEN_MIGRATION = (
    Path(__file__).resolve().parents[1] / "golden" / "expected" / "sample_migration.sql"
)


@pytest.fixture
def sample_config_path() -> Path:
    return SAMPLE_CONFIG


@pytest.fixture
def migration(sample_config_path: Path):
    return BlueprintParser().parse_file(sample_config_path)


@pytest.fixture
def migration_sql(migration) -> str:
    return SqlScriptGenerator().generate(migration).content


@pytest.fixture
def compiler() -> MigrationCompiler:
    return MigrationCompiler(MySqlDialect())


@pytest.fixture
def validation_report(migration):
    return MigrationConfigValidator().validate(migration)
