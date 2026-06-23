"""Integration tests for MSSQL source bootstrap in generated scripts."""

import pytest


@pytest.mark.integration
def test_sample_config_includes_mssql_source_bootstrap(migration_sql: str) -> None:
    assert "-- Bootstrap MSSQL source 'tih'" in migration_sql
    assert "client_billing_mssql.dbo.tbl_invoice_hdr" in migration_sql
    assert "-- Requires ODBC bridge or linked-server mapping" in migration_sql
    assert "`fed_client_billing_mssql`.`tbl_invoice_hdr`" in migration_sql


@pytest.mark.integration
def test_mssql_join_source_gets_separate_bootstrap(migration_sql: str) -> None:
    assert "-- Bootstrap MSSQL source 'til'" in migration_sql
    assert "client_billing_mssql.dbo.tbl_invoice_lines" in migration_sql
    assert "CREATE TEMPORARY TABLE _bootstrap_til" in migration_sql
    assert "CREATE TEMPORARY TABLE _bootstrap_tih" in migration_sql


@pytest.mark.integration
def test_mssql_blueprint_includes_chunking_loop(migration_sql: str) -> None:
    assert "WHILE @bp2_chunk_min <= @bp2_chunk_max DO" in migration_sql
    assert "bp2_chunk_filtered" in migration_sql


@pytest.mark.integration
def test_mssql_connection_variables_emitted(migration_sql: str) -> None:
    assert "SET @tih_host = 'client-billing-ip'" in migration_sql
    assert "SET @tih_port = 1433" in migration_sql
    assert "SET @tih_database = 'finance_db'" in migration_sql
