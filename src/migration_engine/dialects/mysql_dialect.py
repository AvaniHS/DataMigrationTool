"""MySQL dialect implementation — Phase 2 will expand."""

from migration_engine.dialects.base_dialect import BaseDialect
from migration_engine.models.enums import DialectType


class MySqlDialect(BaseDialect):
    """MySQL 8+ dialect string formatter."""

    @property
    def dialect_type(self) -> str:
        return DialectType.MYSQL.value

    def safe_cast(self, expression: str, data_type: str) -> str:
        return f"CAST({expression} AS {data_type})"

    def begin_transaction(self) -> str:
        return "START TRANSACTION;"

    def savepoint(self, name: str) -> str:
        return f"SAVEPOINT {name};"

    def release_savepoint(self, name: str) -> str:
        return f"RELEASE SAVEPOINT {name};"

    def commit(self) -> str:
        return "COMMIT;"
