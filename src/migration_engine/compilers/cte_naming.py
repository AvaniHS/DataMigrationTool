"""Deterministic CTE and bootstrap object naming."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CteNaming:
    """Builds prefixed CTE names for a single blueprint."""

    sequence_order: int

    @property
    def blueprint_prefix(self) -> str:
        return f"bp{self.sequence_order}_"

    def stg(self, alias: str) -> str:
        return f"{self.blueprint_prefix}stg_{alias}"

    def pre_filtered(self, root_alias: str) -> str:
        return f"{self.blueprint_prefix}pre_filtered_{root_alias}"

    def joined(self, root_alias: str) -> str:
        return f"{self.blueprint_prefix}joined_{root_alias}"

    def calculation_layer(self) -> str:
        return f"{self.blueprint_prefix}calculation_layer"

    def filtered_results(self) -> str:
        return f"{self.blueprint_prefix}filtered_results"

    def target_projection(self) -> str:
        return f"{self.blueprint_prefix}target_projection"

    def chunk_filtered(self) -> str:
        return f"{self.blueprint_prefix}chunk_filtered"

    def chunk_savepoint(self) -> str:
        return f"{self.savepoint_name()}_chunk"

    def bootstrap_table(self, alias: str) -> str:
        return f"_bootstrap_{alias}"

    def savepoint_name(self) -> str:
        return f"bp_step_{self.sequence_order}"
