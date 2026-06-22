"""Factory for on_conflict insert strategies."""

from migration_engine.dialects.base_dialect import BaseDialect
from migration_engine.models.enums import ConflictStrategy
from migration_engine.strategies.conflict.base import IConflictStrategy
from migration_engine.strategies.conflict.fail_strategy import FailStrategy
from migration_engine.strategies.conflict.ignore_and_log_strategy import IgnoreAndLogStrategy
from migration_engine.strategies.conflict.ignore_strategy import IgnoreStrategy
from migration_engine.strategies.conflict.ignore_unprocessed_strategy import IgnoreUnprocessedStrategy
from migration_engine.strategies.conflict.upsert_strategy import UpsertStrategy


class ConflictStrategyFactory:
    """Creates conflict strategy implementations."""

    _registry: dict[str, type[IConflictStrategy]] = {
        ConflictStrategy.FAIL.value: FailStrategy,
        ConflictStrategy.IGNORE.value: IgnoreStrategy,
        ConflictStrategy.UPSERT.value: UpsertStrategy,
        ConflictStrategy.IGNORE_AND_LOG.value: IgnoreAndLogStrategy,
        ConflictStrategy.IGNORE_AND_INSERT_UNPROCESSED.value: IgnoreUnprocessedStrategy,
    }

    @classmethod
    def create(cls, strategy: str, dialect: BaseDialect) -> IConflictStrategy:
        strategy_cls = cls._registry.get(strategy.upper())
        if strategy_cls is None:
            supported = ", ".join(sorted(cls._registry))
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
