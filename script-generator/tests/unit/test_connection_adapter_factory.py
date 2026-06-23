"""Unit tests for connection adapter factory and stubs."""

import pytest

from migration_engine.adapters.stub_connection_adapter import StubConnectionAdapter
from migration_engine.factories.connection_adapter_factory import ConnectionAdapterFactory
from migration_engine.models.connection import DatabaseConnection
from migration_engine.models.enums import ConnectionType


def test_factory_returns_stub_for_mysql_connection() -> None:
    connection = DatabaseConnection(
        type=ConnectionType.MYSQL,
        connection_string="mysql://user:pass@host:3306/db",
    )
    adapter = ConnectionAdapterFactory.create("client_crm_mysql", connection)

    assert isinstance(adapter, StubConnectionAdapter)
    assert adapter.connection_ref == "client_crm_mysql"


def test_stub_connect_raises_not_implemented() -> None:
    connection = DatabaseConnection(
        type=ConnectionType.MSSQL,
        connection_string="sqlserver://user:pass@host:1433/db",
    )
    adapter = ConnectionAdapterFactory.create("client_billing_mssql", connection)

    with pytest.raises(NotImplementedError, match="Phase C"):
        adapter.connect()


def test_factory_register_custom_adapter() -> None:
    original = ConnectionAdapterFactory._registry.copy()
    try:
        class RecordingAdapter(StubConnectionAdapter):
            def connect(self) -> None:
                self._connected = True

        ConnectionAdapterFactory.register(ConnectionType.MYSQL.value, RecordingAdapter)
        connection = DatabaseConnection(
            type=ConnectionType.MYSQL,
            connection_string="mysql://user:pass@host:3306/db",
        )
        adapter = ConnectionAdapterFactory.create("test_mysql", connection)

        assert isinstance(adapter, RecordingAdapter)
        adapter.connect()
        assert adapter._connected is True
    finally:
        ConnectionAdapterFactory._registry.clear()
        ConnectionAdapterFactory._registry.update(original)
