"""Tests for user-facing connection error sanitization."""

from config_platform_api.connectors.sql_helpers import sanitize_connection_error


def test_sanitize_odbc_driver_missing() -> None:
    raw = (
        "(pyodbc.InterfaceError) ('IM002', '[IM002] [Microsoft][ODBC Driver Manager] "
        "Data source name not found and no default driver specified (0) (SQLDriverConnect)') "
        "(Background on this error at: https://sqlalche.me/e/20/rvf5)"
    )
    message = sanitize_connection_error(raw)
    assert "ODBC driver" in message
    assert "sqlalche.me" not in message


def test_sanitize_login_failure() -> None:
    message = sanitize_connection_error("Login failed for user 'bad_user'")
    assert message == "Connection failed. Check host, credentials, and network access."


def test_sanitize_s3_access_denied() -> None:
    message = sanitize_connection_error("An error occurred (AccessDenied) when calling the HeadBucket operation")
    assert "S3 connection failed" in message
