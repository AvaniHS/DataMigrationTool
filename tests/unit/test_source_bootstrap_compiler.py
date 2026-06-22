"""Unit tests for source bootstrap compiler."""

from pathlib import Path

import pytest

from migration_engine.compilers.bootstrap.source_bootstrap_compiler import SourceBootstrapCompiler
from migration_engine.parsers.blueprint_parser import BlueprintParser

SAMPLE_CONFIG = Path(__file__).resolve().parents[2] / "docs" / "sampleConfigfile.json"


@pytest.fixture
def migration():
    return BlueprintParser().parse_file(SAMPLE_CONFIG)


@pytest.fixture
def bootstrap_compiler() -> SourceBootstrapCompiler:
    return SourceBootstrapCompiler()


def test_blueprint_one_bootstrap_contains_mysql_and_csv_sources(
    migration, bootstrap_compiler: SourceBootstrapCompiler
) -> None:
    blueprint = migration.blueprints[0]
    preamble = bootstrap_compiler.build(blueprint, migration.connections)

    assert "Bootstrap MYSQL source 'cm'" in preamble
    assert "CREATE TEMPORARY TABLE _bootstrap_cm AS" in preamble
    assert "fed_client_crm_mysql" in preamble
    assert "Bootstrap CSV source 'gam'" in preamble
    assert "CREATE TEMPORARY TABLE _bootstrap_gam AS" in preamble
    assert "@gam_s3_uri" in preamble


def test_blueprint_two_bootstrap_contains_mssql_and_postgresql_sources(
    migration, bootstrap_compiler: SourceBootstrapCompiler
) -> None:
    blueprint = migration.blueprints[1]
    preamble = bootstrap_compiler.build(blueprint, migration.connections)

    assert "Bootstrap MSSQL source 'tih'" in preamble
    assert "CREATE TEMPORARY TABLE _bootstrap_tih AS" in preamble
    assert "Bootstrap MSSQL source 'til'" in preamble
    assert "Bootstrap POSTGRESQL source 'st'" in preamble
    assert "@st_host" in preamble


def test_bootstrap_emits_connection_variables_for_database_sources(
    migration, bootstrap_compiler: SourceBootstrapCompiler
) -> None:
    blueprint = migration.blueprints[0]
    preamble = bootstrap_compiler.build(blueprint, migration.connections)

    assert "@cm_host = 'client-crm-ip'" in preamble
    assert "@cm_database = 'crm_db'" in preamble
