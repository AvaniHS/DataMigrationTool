"""Application-wide exception types."""


class ConnectionStoreError(Exception):
    """Raised when the connection registry cannot be read or written."""


class MigrationStoreError(Exception):
    """Raised when the migration registry cannot be read or written."""


class IntrospectionError(Exception):
    """Raised when schema introspection fails."""


class DdlError(Exception):
    """Raised when target DDL operations fail."""
