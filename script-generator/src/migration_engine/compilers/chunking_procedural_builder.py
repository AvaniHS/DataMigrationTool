"""Chunking procedural loop SQL generation."""

from migration_engine.compilers.cte_naming import CteNaming
from migration_engine.dialects.base_dialect import BaseDialect
from migration_engine.models.blueprint import Blueprint


class ChunkingProceduralBuilder:
    """Wraps blueprint load SQL in a parameterized chunking loop."""

    def __init__(self, dialect: BaseDialect) -> None:
        self._dialect = dialect

    def build_setup_statements(self, blueprint: Blueprint) -> str:
        """Emit session variables used by the chunking loop."""
        if not blueprint.chunking_strategy.is_enabled:
            return ""

        naming = CteNaming(blueprint.sequence_order)
        chunking = blueprint.chunking_strategy
        root_alias = blueprint.sources.root_table.alias
        bootstrap_table = naming.bootstrap_table(root_alias)
        chunk_column = chunking.chunk_by_column
        prefix = naming.blueprint_prefix.rstrip("_")

        if not chunk_column or chunking.chunk_size is None:
            raise ValueError("Chunking requires chunk_by_column and chunk_size.")

        return "\n".join(
            [
                f"SET @{prefix}_chunk_min = 0;",
                f"SET @{prefix}_chunk_size = {chunking.chunk_size};",
                (
                    f"SET @{prefix}_chunk_max = ("
                    f"SELECT COALESCE(MAX({chunk_column}), 0) "
                    f"FROM {bootstrap_table} AS {root_alias}"
                    f");"
                ),
            ]
        )

    def wrap_in_chunk_loop(self, blueprint: Blueprint, inner_sql: str) -> str:
        """Wrap CTE + INSERT SQL in a WHILE loop with per-chunk savepoints."""
        if not blueprint.chunking_strategy.is_enabled:
            return inner_sql

        naming = CteNaming(blueprint.sequence_order)
        prefix = naming.blueprint_prefix.rstrip("_")
        chunk_min = f"@{prefix}_chunk_min"
        chunk_max = f"@{prefix}_chunk_max"
        chunk_size = f"@{prefix}_chunk_size"
        chunk_savepoint = naming.chunk_savepoint()

        return "\n".join(
            [
                f"WHILE {chunk_min} <= {chunk_max} DO",
                self._dialect.savepoint(chunk_savepoint),
                inner_sql.strip().rstrip(";"),
                ";",
                f"SET {chunk_min} = {chunk_min} + {chunk_size};",
                self._dialect.release_savepoint(chunk_savepoint),
                "END WHILE;",
            ]
        )
