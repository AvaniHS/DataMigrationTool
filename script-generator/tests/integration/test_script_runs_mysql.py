"""Integration tests for MySQL source bootstrap in generated scripts."""

import pytest

from migration_engine.models.enums import ConnectionType


@pytest.mark.integration
def test_sample_config_includes_mysql_source_bootstrap(migration_sql: str) -> None:
    assert "-- Bootstrap MYSQL source 'cm'" in migration_sql
    assert "client_crm_mysql.crm_db.customer_master" in migration_sql
    assert "`fed_client_crm_mysql`.`customer_master`" in migration_sql
    assert "SET @cm_host = 'client-crm-ip'" in migration_sql
    assert "CREATE TEMPORARY TABLE _bootstrap_cm" in migration_sql


@pytest.mark.integration
def test_mysql_bootstrap_uses_federated_schema_naming(migration_sql: str) -> None:
    assert "fed_client_crm_mysql" in migration_sql
    assert ConnectionType.MYSQL.value in migration_sql or "MYSQL source" in migration_sql


@pytest.mark.integration
@pytest.mark.parametrize("alias", ["cm"])
def test_mysql_source_temp_table_referenced_in_cte(migration_sql: str, alias: str) -> None:
    assert f"_bootstrap_{alias}" in migration_sql
    assert f"stg_{alias}" in migration_sql
