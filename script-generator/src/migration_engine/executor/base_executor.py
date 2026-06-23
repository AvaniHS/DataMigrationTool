"""Migration executor interface — Phase C."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from pathlib import Path

from migration_engine.executor.models import BatchMetrics, ExecutionReport, RowErrorLedgerEntry


class IExecutor(ABC):
    """Runs generated migration scripts against a target environment.

  Phase C implementations execute blueprint steps in order, stream source rows
  through connection adapters in bounded batches, and emit structured telemetry.
  See ``docs/executor-streaming-design.md`` for streaming hook contracts.
    """

    @abstractmethod
    def execute(self, script_path: Path) -> ExecutionReport:
        """Execute a generated SQL script file and return structured telemetry."""

    @abstractmethod
    def execute_text(self, migration_id: str, script_content: str) -> ExecutionReport:
        """Execute inline SQL script content (used in tests and dry-runs)."""

    @abstractmethod
    def stream_batches(
        self,
        blueprint_sequence: int,
        batch_size: int,
    ) -> Iterator[BatchMetrics]:
        """Yield per-batch metrics while a blueprint step streams rows.

        Hook for Phase C Python-side staging when SQL-only bootstrap is not used.
        Default implementations may raise ``NotImplementedError``.
        """

    def on_row_error(
        self,
        handler: Callable[[RowErrorLedgerEntry], None],
    ) -> None:
        """Register a callback invoked for each row-level failure.

        Executors must continue processing remaining rows after logging an error.
        """
