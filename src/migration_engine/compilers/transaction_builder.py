"""Transaction and savepoint SQL generation."""

from migration_engine.compilers.cte_naming import CteNaming
from migration_engine.dialects.base_dialect import BaseDialect


class TransactionBuilder:
    """Wraps a blueprint SQL block in per-step transaction boundaries."""

    def __init__(self, dialect: BaseDialect) -> None:
        self._dialect = dialect

    def wrap_blueprint_block(self, sequence_order: int, body: str) -> str:
        """Wrap SQL in START TRANSACTION → SAVEPOINT → body → RELEASE → COMMIT."""
        naming = CteNaming(sequence_order)
        savepoint = naming.savepoint_name()
        sections = [
            self._dialect.begin_transaction(),
            self._dialect.savepoint(savepoint),
            body.strip(),
            self._dialect.release_savepoint(savepoint),
            self._dialect.commit(),
        ]
        return "\n\n".join(sections)
