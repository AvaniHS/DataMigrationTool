"""Connection adapter DTOs — Phase C execution layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AdapterBatch:
    """One streamed batch of rows from a source query."""

    batch_number: int
    row_count: int
    rows: tuple[dict[str, Any], ...]


@dataclass
class AdapterHealth:
    """Connectivity probe result for a connection adapter."""

    connection_ref: str
    is_reachable: bool
    message: str = ""


@dataclass
class RowErrorEntry:
    """Row-level failure captured during adapter streaming."""

    connection_ref: str
    row_identity: dict[str, Any]
    error_code: str
    message: str


@dataclass
class AdapterStreamMetrics:
    """Telemetry emitted while an adapter streams batches."""

    connection_ref: str
    batches_read: int = 0
    rows_read: int = 0
    errors: list[RowErrorEntry] = field(default_factory=list)
