from enum import Enum


class ConnectionType(str, Enum):
    MYSQL = "MYSQL"
    MSSQL = "MSSQL"
    POSTGRESQL = "POSTGRESQL"
    CSV_S3_BUCKET = "CSV_S3_BUCKET"


class OnConflictStrategy(str, Enum):
    FAIL = "FAIL"
    IGNORE = "IGNORE"
    UPSERT = "UPSERT"
    IGNORE_AND_LOG = "IGNORE_AND_LOG"
    IGNORE_AND_INSERT_UNPROCESSED = "IGNORE_AND_INSERT_UNPROCESSED"
