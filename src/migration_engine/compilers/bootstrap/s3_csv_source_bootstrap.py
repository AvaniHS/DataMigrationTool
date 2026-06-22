"""Bootstrap strategy for S3 CSV sources."""

from migration_engine.compilers.bootstrap._sql_helpers import (
    federated_schema_name,
    sanitize_identifier,
)
from migration_engine.compilers.bootstrap.base_bootstrap import ISourceBootstrapStrategy
from migration_engine.compilers.bootstrap.context import SourceBootstrapRequest
from migration_engine.models.connection import CsvS3Connection


class S3CsvSourceBootstrapStrategy(ISourceBootstrapStrategy):
    """Bootstrap a CSV file staged from S3 into a temporary table."""

    def build_preamble(self, request: SourceBootstrapRequest) -> str:
        source = request.source
        connection = request.connection
        if not isinstance(connection, CsvS3Connection):
            raise TypeError("S3 CSV source bootstrap requires a CSV_S3_BUCKET connection.")

        if not source.file_name:
            raise ValueError(f"S3 CSV source '{source.alias}' requires file_name.")

        staging_schema = federated_schema_name(source.connection_ref)
        staging_table = sanitize_identifier(source.file_name)
        local_path = f"/tmp/migration/{source.file_name}"

        lines = [
            f"-- Bootstrap CSV source '{source.alias}' ({source.file_name})",
            f"SET @{source.alias}_s3_uri = '{connection.s3_bucket_uri}{source.file_name}';",
            f"SET @{source.alias}_aws_region = '{connection.aws_region}';",
            f"SET @{source.alias}_local_csv = '{local_path}';",
            "-- Pre-step: download CSV from S3 to @alias_local_csv before executing this script.",
            f"DROP TEMPORARY TABLE IF EXISTS {source.bootstrap_table};",
            (
                f"CREATE TEMPORARY TABLE {source.bootstrap_table} AS\n"
                f"SELECT *\n"
                f"FROM `{staging_schema}`.`{staging_table}`;"
            ),
            (
                f"-- Alternate local load path:\n"
                f"-- LOAD DATA LOCAL INFILE @{source.alias}_local_csv\n"
                f"-- INTO TABLE {source.bootstrap_table}\n"
                f"-- FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"'\n"
                f"-- LINES TERMINATED BY '\\n' IGNORE 1 ROWS;"
            ),
        ]
        return "\n".join(lines)
