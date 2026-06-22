"""Shared enumerations for the migration engine."""

from enum import StrEnum


class ConnectionType(StrEnum):
    MYSQL = "MYSQL"
    MSSQL = "MSSQL"
    POSTGRESQL = "POSTGRESQL"
    CSV_S3_BUCKET = "CSV_S3_BUCKET"


class OutputFormat(StrEnum):
    SQL = "SQL"


class SourceType(StrEnum):
    DIRECT = "DIRECT"
    DERIVED = "DERIVED"
    EXPRESSION = "EXPRESSION"
    CONSTANT = "CONSTANT"


class ConflictStrategy(StrEnum):
    FAIL = "FAIL"
    IGNORE = "IGNORE"
    UPSERT = "UPSERT"
    IGNORE_AND_LOG = "IGNORE_AND_LOG"
    IGNORE_AND_INSERT_UNPROCESSED = "IGNORE_AND_INSERT_UNPROCESSED"


class JoinType(StrEnum):
    INNER = "INNER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    FULL = "FULL"


class DialectType(StrEnum):
    MYSQL = "MYSQL"
    POSTGRESQL = "POSTGRESQL"
    ORACLE = "ORACLE"
