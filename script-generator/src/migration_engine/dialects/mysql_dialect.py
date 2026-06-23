"""MySQL 8+ dialect string formatting utilities."""

import re

from migration_engine.dialects.base_dialect import BaseDialect
from migration_engine.models.enums import DialectType

_NUMERIC_PATTERN = r"^-?[0-9]+(\.[0-9]+)?$"
_INTEGER_PATTERN = r"^-?[0-9]+$"
_UUID_PATTERN = r"^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$"


class MySqlDialect(BaseDialect):
    """MySQL 8+ dialect string formatter."""

    @property
    def dialect_type(self) -> str:
        return DialectType.MYSQL.value

    def safe_cast(self, expression: str, data_type: str) -> str:
        base_type = self._base_type(data_type)

        if base_type in {"VARCHAR", "CHAR", "TEXT"}:
            return f"NULLIF(TRIM(CAST({expression} AS CHAR)), '')"

        if base_type == "UUID":
            return (
                f"CASE WHEN {expression} IS NULL OR TRIM({expression}) = '' THEN NULL "
                f"WHEN TRIM({expression}) REGEXP '{_UUID_PATTERN}' THEN TRIM({expression}) "
                f"ELSE NULL END"
            )

        if base_type in {"INT", "INTEGER", "BIGINT"}:
            return (
                f"CASE WHEN {expression} IS NULL OR TRIM({expression}) = '' THEN NULL "
                f"WHEN TRIM(CAST({expression} AS CHAR)) REGEXP '{_INTEGER_PATTERN}' "
                f"THEN CAST({expression} AS {data_type}) ELSE NULL END"
            )

        if base_type in {"DECIMAL", "DOUBLE", "FLOAT"}:
            return (
                f"CASE WHEN {expression} IS NULL OR TRIM({expression}) = '' THEN NULL "
                f"WHEN TRIM(CAST({expression} AS CHAR)) REGEXP '{_NUMERIC_PATTERN}' "
                f"THEN CAST({expression} AS {data_type}) ELSE NULL END"
            )

        if base_type == "DATE":
            return (
                f"CASE WHEN {expression} IS NULL OR TRIM({expression}) = '' THEN NULL "
                f"ELSE STR_TO_DATE({expression}, '%Y-%m-%d') END"
            )

        if base_type in {"DATETIME", "TIMESTAMP"}:
            return (
                f"CASE WHEN {expression} IS NULL OR TRIM({expression}) = '' THEN NULL "
                f"ELSE STR_TO_DATE({expression}, '%Y-%m-%d %H:%i:%s') END"
            )

        return f"CAST({expression} AS {data_type})"

    def qualify_table(self, schema: str, table: str) -> str:
        return f"{schema}.{table}"

    def concat(self, *expressions: str) -> str:
        if not expressions:
            raise ValueError("concat() requires at least one expression.")
        if len(expressions) == 1:
            return expressions[0]
        joined = ", ".join(expressions)
        return f"CONCAT({joined})"

    def regexp_replace(self, expression: str, pattern: str, replacement: str) -> str:
        return f"REGEXP_REPLACE({expression}, '{pattern}', '{replacement}')"

    def on_duplicate_key_update(self, columns: list[str], primary_keys: list[str]) -> str:
        primary_key_set = set(primary_keys)
        update_columns = [column for column in columns if column not in primary_key_set]
        if not update_columns:
            # MySQL requires at least one update expression; no-op update on first PK.
            first_key = primary_keys[0]
            return f"ON DUPLICATE KEY UPDATE {first_key} = {first_key}"

        assignments = ", ".join(
            f"{column} = VALUES({column})" for column in update_columns
        )
        return f"ON DUPLICATE KEY UPDATE {assignments}"

    def primary_key_join(
        self, left_alias: str, right_alias: str, primary_keys: list[str]
    ) -> str:
        if not primary_keys:
            raise ValueError("primary_key_join() requires at least one primary key column.")

        predicates = [
            f"{left_alias}.{column} = {right_alias}.{column}" for column in primary_keys
        ]
        return " AND ".join(predicates)

    def begin_transaction(self) -> str:
        return "START TRANSACTION;"

    def savepoint(self, name: str) -> str:
        return f"SAVEPOINT {name};"

    def release_savepoint(self, name: str) -> str:
        return f"RELEASE SAVEPOINT {name};"

    def rollback_to_savepoint(self, name: str) -> str:
        return f"ROLLBACK TO SAVEPOINT {name};"

    def commit(self) -> str:
        return "COMMIT;"

    def _base_type(self, data_type: str) -> str:
        normalized = data_type.strip().upper()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.split("(", 1)[0].strip()
