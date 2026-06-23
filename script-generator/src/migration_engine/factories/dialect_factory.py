"""Factory for SQL dialect implementations."""

from migration_engine.dialects.base_dialect import BaseDialect
from migration_engine.dialects.mysql_dialect import MySqlDialect
from migration_engine.models.enums import DialectType


class DialectFactory:
    """Creates dialect implementations by type."""

    _registry: dict[str, type[BaseDialect]] = {
        DialectType.MYSQL.value: MySqlDialect,
    }

    @classmethod
    def create(cls, dialect_type: str) -> BaseDialect:
        dialect_cls = cls._registry.get(dialect_type.upper())
        if dialect_cls is None:
            supported = ", ".join(sorted(cls._registry))
            raise ValueError(
                f"Unsupported dialect '{dialect_type}'. Supported: {supported}"
            )
        return dialect_cls()

    @classmethod
    def register(cls, dialect_type: str, dialect_cls: type[BaseDialect]) -> None:
        cls._registry[dialect_type.upper()] = dialect_cls
