"""Not-implemented connection adapter — Phase C placeholder."""

from __future__ import annotations

from collections.abc import Iterator

from migration_engine.adapters.base_adapter import IConnectionAdapter
from migration_engine.adapters.models import AdapterBatch, AdapterHealth
from migration_engine.models.enums import ConnectionType


class StubConnectionAdapter(IConnectionAdapter):
    """Placeholder adapter registered for every connection type in Phase C."""

    def __init__(self, connection_ref: str, connection_type: ConnectionType) -> None:
        self._connection_ref = connection_ref
        self._connection_type = connection_type

    @property
    def connection_ref(self) -> str:
        return self._connection_ref

    def connect(self) -> None:
        raise NotImplementedError(
            f"Connection adapter for '{self._connection_ref}' ({self._connection_type.value}) "
            "is not implemented. Phase C will provide streaming adapters."
        )

    def health_check(self) -> AdapterHealth:
        raise NotImplementedError(
            f"Health check for '{self._connection_ref}' is not implemented (Phase C)."
        )

    def fetch_batch(self, query: str, batch_size: int) -> Iterator[AdapterBatch]:
        raise NotImplementedError(
            f"Streaming fetch for '{self._connection_ref}' is not implemented (Phase C)."
        )
        yield AdapterBatch(batch_number=0, row_count=0, rows=())  # pragma: no cover

    def execute(self, statement: str) -> None:
        raise NotImplementedError(
            f"Execute for '{self._connection_ref}' is not implemented (Phase C)."
        )

    def close(self) -> None:
        return None
