"""Unit tests for connection string parsing."""

import pytest

from migration_engine.compilers.bootstrap.connection_string_parser import (
    parse_database_connection_string,
)


def test_parse_mysql_connection_string() -> None:
    params = parse_database_connection_string(
        "mysql://read_user:pass@client-crm-ip:3306/crm_db"
    )

    assert params.scheme == "mysql"
    assert params.host == "client-crm-ip"
    assert params.port == 3306
    assert params.username == "read_user"
    assert params.password == "pass"
    assert params.database == "crm_db"


def test_parse_sqlserver_connection_string() -> None:
    params = parse_database_connection_string(
        "sqlserver://read_user:pass@client-billing-ip:1433/finance_db"
    )

    assert params.scheme == "sqlserver"
    assert params.host == "client-billing-ip"
    assert params.port == 1433
    assert params.database == "finance_db"


def test_parse_connection_string_without_database_raises() -> None:
    with pytest.raises(ValueError, match="database name"):
        parse_database_connection_string("mysql://user:pass@host:3306/")
