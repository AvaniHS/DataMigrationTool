"""Parsed database connection parameters."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConnectionParams:
    """Normalized parameters extracted from a database connection string."""

    scheme: str
    host: str
    port: int
    username: str
    password: str
    database: str
