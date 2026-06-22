"""Connection adapter interface — Phase C."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any


class IConnectionAdapter(ABC):
    """Executes queries against a source or target system."""

    @abstractmethod
    def connect(self) -> None:
        """Open the connection."""

    @abstractmethod
    def fetch_batch(self, query: str, batch_size: int) -> Iterator[dict[str, Any]]:
        """Stream result rows in batches."""

    @abstractmethod
    def close(self) -> None:
        """Close the connection and release resources."""
