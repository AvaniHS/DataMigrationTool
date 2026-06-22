"""Abstract base dialect for SQL string formatting."""

from abc import ABC, abstractmethod


class BaseDialect(ABC):
    """Stateless dialect contract — pure string formatting only."""

    @property
    @abstractmethod
    def dialect_type(self) -> str:
        """Return the dialect identifier (e.g. MYSQL)."""

    @abstractmethod
    def safe_cast(self, expression: str, data_type: str) -> str:
        """Return a dialect-specific safe cast expression."""

    @abstractmethod
    def begin_transaction(self) -> str:
        """Return a BEGIN/START TRANSACTION statement."""

    @abstractmethod
    def savepoint(self, name: str) -> str:
        """Return a SAVEPOINT statement."""

    @abstractmethod
    def release_savepoint(self, name: str) -> str:
        """Return a RELEASE SAVEPOINT statement."""

    @abstractmethod
    def commit(self) -> str:
        """Return a COMMIT statement."""
