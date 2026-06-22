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
    def qualify_table(self, schema: str, table: str) -> str:
        """Return a fully qualified table reference."""

    @abstractmethod
    def concat(self, *expressions: str) -> str:
        """Return a dialect-specific string concatenation expression."""

    @abstractmethod
    def regexp_replace(self, expression: str, pattern: str, replacement: str) -> str:
        """Return a dialect-specific regexp replace expression."""

    @abstractmethod
    def on_duplicate_key_update(self, columns: list[str], primary_keys: list[str]) -> str:
        """Return an UPSERT suffix for the given columns and primary keys."""

    @abstractmethod
    def primary_key_join(
        self, left_alias: str, right_alias: str, primary_keys: list[str]
    ) -> str:
        """Return an equi-join predicate across primary key columns."""

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
    def rollback_to_savepoint(self, name: str) -> str:
        """Return a ROLLBACK TO SAVEPOINT statement."""

    @abstractmethod
    def commit(self) -> str:
        """Return a COMMIT statement."""
