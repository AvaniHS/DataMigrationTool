"""Parse database connection strings into structured parameters."""

from urllib.parse import unquote, urlparse

from migration_engine.compilers.bootstrap.models import DatabaseConnectionParams

_DEFAULT_PORTS = {
    "mysql": 3306,
    "postgresql": 5432,
    "postgres": 5432,
    "sqlserver": 1433,
    "mssql": 1433,
}


def parse_database_connection_string(connection_string: str) -> DatabaseConnectionParams:
    """Parse a URL-style database connection string."""
    parsed = urlparse(connection_string)
    scheme = (parsed.scheme or "mysql").lower()
    host = parsed.hostname or "localhost"
    port = parsed.port or _DEFAULT_PORTS.get(scheme, 3306)
    username = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    database = unquote(parsed.path.lstrip("/")) if parsed.path else ""

    if not database:
        raise ValueError(f"Connection string for '{scheme}' must include a database name.")

    return DatabaseConnectionParams(
        scheme=scheme,
        host=host,
        port=port,
        username=username,
        password=password,
        database=database,
    )
