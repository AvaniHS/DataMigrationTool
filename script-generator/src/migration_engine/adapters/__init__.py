"""Connection adapters — Phase C execution layer."""

from migration_engine.adapters.base_adapter import IConnectionAdapter
from migration_engine.adapters.models import AdapterBatch, AdapterHealth, RowErrorEntry
from migration_engine.adapters.stub_connection_adapter import StubConnectionAdapter

__all__ = [
    "AdapterBatch",
    "AdapterHealth",
    "IConnectionAdapter",
    "RowErrorEntry",
    "StubConnectionAdapter",
]
