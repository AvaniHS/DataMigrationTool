"""Source bootstrap context for preamble generation."""

from dataclasses import dataclass

from migration_engine.models.connection import ConnectionConfig
from migration_engine.models.enums import ConnectionType


@dataclass(frozen=True)
class SourceBootstrapContext:
    """Resolved source metadata required to build a bootstrap preamble."""

    alias: str
    connection_ref: str
    connection_type: ConnectionType
    bootstrap_table: str
    schema_name: str | None = None
    table_name: str | None = None
    file_name: str | None = None
    comment: str | None = None


@dataclass(frozen=True)
class SourceBootstrapRequest:
    """Input bundle for a bootstrap strategy."""

    source: SourceBootstrapContext
    connection: ConnectionConfig
