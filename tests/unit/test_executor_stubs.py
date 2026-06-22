"""Unit tests for executor stubs."""

from pathlib import Path

import pytest

from migration_engine.executor.models import ExecutionReport, RowErrorLedgerEntry
from migration_engine.executor.stub_executor import StubExecutor


def test_stub_executor_execute_raises() -> None:
    executor = StubExecutor()

    with pytest.raises(NotImplementedError, match="Script execution is not implemented"):
        executor.execute(Path("output/migration.sql"))


def test_stub_executor_stream_batches_raises() -> None:
    executor = StubExecutor()

    with pytest.raises(NotImplementedError, match="Batch streaming"):
        next(executor.stream_batches(blueprint_sequence=2, batch_size=1000))


def test_execution_report_serializes_row_errors() -> None:
    report = ExecutionReport(
        migration_id="mig_test",
        success=False,
        row_errors=[
            RowErrorLedgerEntry(
                blueprint_sequence=1,
                batch_number=3,
                row_identity={"id": "abc"},
                error_code="CAST_FAILED",
                message="Invalid UUID",
            )
        ],
    )

    payload = report.to_dict()

    assert payload["row_error_count"] == 1
    assert payload["row_errors"][0]["error_code"] == "CAST_FAILED"
