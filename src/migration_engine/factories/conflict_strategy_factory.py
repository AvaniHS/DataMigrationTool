"""Factory for on_conflict insert strategies — Phase 2."""

from migration_engine.dialects.base_dialect import BaseDialect
from migration_engine.models.enums import ConflictStrategy
from migration_engine.strategies.conflict.base import IConflictStrategy


class ConflictStrategyFactory:
    """Creates conflict strategy implementations."""

    _registry: dict[str, type[IConflictStrategy]] = {}

    @classmethod
    def create(cls, strategy: str, dialect: BaseDialect) -> IConflictStrategy:
        strategy_cls = cls._registry.get(strategy.upper())
        if strategy_cls is None:
            supported = ", ".join(sorted(cls._registry)) or "(none registered yet)"
            raise ValueError(
                f"Unsupported conflict strategy '{strategy}'. Supported: {supported}"
            )
        return strategy_cls(dialect)

    @classmethod
    def register(cls, strategy: str, strategy_cls: type[IConflictStrategy]) -> None:
        cls._registry[strategy.upper()] = strategy_cls

    @classmethod
    def supported_strategies(cls) -> frozenset[str]:
        return frozenset(cls._registry)
