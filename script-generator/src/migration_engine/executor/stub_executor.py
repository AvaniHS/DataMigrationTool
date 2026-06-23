"""Not-implemented migration executor — Phase C placeholder."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

from migration_engine.executor.base_executor import IExecutor
from migration_engine.executor.models import BatchMetrics, ExecutionReport, RowErrorLedgerEntry


class StubExecutor(IExecutor):
    """Placeholder executor that documents the Phase C contract."""

    def execute(self, script_path: Path) -> ExecutionReport:
        raise NotImplementedError(
            f"Script execution is not implemented (Phase C). Path: {script_path}"
        )

    def execute_text(self, migration_id: str, script_content: str) -> ExecutionReport:
        raise NotImplementedError(
            f"Inline script execution is not implemented (Phase C). Migration: {migration_id}"
        )

    def stream_batches(
        self,
        blueprint_sequence: int,
        batch_size: int,
    ) -> Iterator[BatchMetrics]:
        raise NotImplementedError(
            f"Batch streaming for blueprint {blueprint_sequence} is not implemented (Phase C)."
        )
        yield BatchMetrics(  # pragma: no cover
            blueprint_sequence=blueprint_sequence,
            batch_number=0,
            rows_processed=0,
            duration_ms=0.0,
        )

    def on_row_error(self, handler: Callable[[RowErrorLedgerEntry], None]) -> None:
        self._row_error_handler = handler
