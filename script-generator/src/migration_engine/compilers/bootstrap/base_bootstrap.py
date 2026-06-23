"""Source bootstrap strategy interface."""

from abc import ABC, abstractmethod

from migration_engine.compilers.bootstrap.context import SourceBootstrapRequest


class ISourceBootstrapStrategy(ABC):
    """Builds SQL preamble statements for a single source alias."""

    @abstractmethod
    def build_preamble(self, request: SourceBootstrapRequest) -> str:
        """Return SQL statements that populate the bootstrap temporary table."""
