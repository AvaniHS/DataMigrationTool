"""Unit tests for Phase 0 factories and stubs."""

import pytest

from migration_engine.factories.dialect_factory import DialectFactory
from migration_engine.factories.script_generator_factory import ScriptGeneratorFactory
from migration_engine.generators.sql_script_generator import SqlScriptGenerator
from migration_engine.models.enums import DialectType, OutputFormat


def test_script_generator_factory_returns_sql_generator() -> None:
    generator = ScriptGeneratorFactory.create(OutputFormat.SQL.value)
    assert isinstance(generator, SqlScriptGenerator)


def test_script_generator_factory_unknown_format_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported output format"):
        ScriptGeneratorFactory.create("XML")


def test_dialect_factory_returns_mysql_dialect() -> None:
    dialect = DialectFactory.create(DialectType.MYSQL.value)
    assert dialect.dialect_type == DialectType.MYSQL.value


def test_dialect_factory_unknown_dialect_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported dialect"):
        DialectFactory.create("DB2")
