"""Factory for connection adapter implementations — Phase C."""

from migration_engine.adapters.base_adapter import IConnectionAdapter
from migration_engine.adapters.stub_connection_adapter import StubConnectionAdapter
from migration_engine.models.connection import ConnectionConfig, CsvS3Connection, DatabaseConnection
from migration_engine.models.enums import ConnectionType


class ConnectionAdapterFactory:
    """Creates connection adapters by connection type.

    v1 registers ``StubConnectionAdapter`` for all supported connection types.
    Phase C replaces stubs with MySQL, MSSQL, PostgreSQL, and S3 implementations
  via ``register()``.
    """

    _registry: dict[str, type[IConnectionAdapter]] = {}

    @classmethod
    def create(cls, connection_ref: str, connection: ConnectionConfig) -> IConnectionAdapter:
        connection_type = cls._resolve_connection_type(connection)
        adapter_cls = cls._registry.get(connection_type)
        if adapter_cls is None:
            return StubConnectionAdapter(connection_ref, ConnectionType(connection_type))
        return adapter_cls(connection_ref, connection)  # type: ignore[call-arg]

    @classmethod
    def register(
        cls,
        connection_type: str,
        adapter_cls: type[IConnectionAdapter],
    ) -> None:
        cls._registry[connection_type.upper()] = adapter_cls

    @classmethod
    def _resolve_connection_type(cls, connection: ConnectionConfig) -> str:
        if isinstance(connection, DatabaseConnection):
            return connection.type.value
        if isinstance(connection, CsvS3Connection):
            return connection.type.value
        raise TypeError(f"Unsupported connection config type: {type(connection)!r}")
