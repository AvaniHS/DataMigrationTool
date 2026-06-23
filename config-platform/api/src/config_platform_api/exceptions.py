"""Application-wide exception types."""


class ConnectionStoreError(Exception):
    """Raised when the connection registry cannot be read or written."""
