"""Connection adapter interface — Phase C."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from types import TracebackType

from migration_engine.adapters.models import AdapterBatch, AdapterHealth


class IConnectionAdapter(ABC):
    """Executes queries against a source or target system.

  Phase C implementations must stream rows in bounded batches and never load an
  entire source table into memory. Use ``fetch_batch`` as the primary read path.
    """

    @property
    @abstractmethod
    def connection_ref(self) -> str:
        """Logical connection name from the migration config."""

    @abstractmethod
    def connect(self) -> None:
        """Open the connection and validate credentials."""

    @abstractmethod
    def health_check(self) -> AdapterHealth:
        """Verify reachability without running migration queries."""

    @abstractmethod
    def fetch_batch(self, query: str, batch_size: int) -> Iterator[AdapterBatch]:
        """Stream result rows in bounded batches.

        Implementations should use server-side cursors or ``LIMIT/OFFSET`` (or
        dialect equivalent) so each yielded batch fits within ``batch_size``.
        """

    @abstractmethod
    def execute(self, statement: str) -> None:
        """Run a non-query statement (DDL/DML) on the connected system."""

    @abstractmethod
    def close(self) -> None:
        """Close the connection and release resources."""

    def __enter__(self) -> IConnectionAdapter:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
