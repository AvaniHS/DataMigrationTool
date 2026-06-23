from enum import StrEnum


class ConnectionType(StrEnum):
    MYSQL = "MYSQL"
    MSSQL = "MSSQL"
    POSTGRESQL = "POSTGRESQL"
    CSV_S3_BUCKET = "CSV_S3_BUCKET"
