"""Migration executor DTOs — Phase C."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BatchMetrics:
    """Per-batch execution telemetry."""

    blueprint_sequence: int
    batch_number: int
    rows_processed: int
    duration_ms: float


@dataclass
class RowErrorLedgerEntry:
    """Row-level failure recorded during executor streaming."""

    blueprint_sequence: int
    batch_number: int
    row_identity: dict[str, Any]
    error_code: str
    message: str


@dataclass
class ExecutionReport:
    """Aggregated outcome of a migration script run."""

    migration_id: str
    success: bool
    blueprints_completed: int = 0
    rows_processed: int = 0
    batches_processed: int = 0
    row_errors: list[RowErrorLedgerEntry] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "migration_id": self.migration_id,
            "success": self.success,
            "blueprints_completed": self.blueprints_completed,
            "rows_processed": self.rows_processed,
            "batches_processed": self.batches_processed,
            "row_error_count": len(self.row_errors),
            "row_errors": [
                {
                    "blueprint_sequence": entry.blueprint_sequence,
                    "batch_number": entry.batch_number,
                    "row_identity": entry.row_identity,
                    "error_code": entry.error_code,
                    "message": entry.message,
                }
                for entry in self.row_errors
            ],
            "message": self.message,
        }
