# Executor Streaming Design (Phase C)

This document describes how the Phase C Python executor will stream data without
loading entire source tables into memory.

## Goals

- Bounded memory per blueprint step regardless of source row count
- Row-level error isolation with a structured error ledger
- Idempotent re-runs compatible with generated SQL savepoints
- Pluggable connection adapters via `ConnectionAdapterFactory`

## Streaming hooks

| Hook | Owner | Responsibility |
|------|-------|----------------|
| `IConnectionAdapter.fetch_batch()` | Adapter | Read `batch_size` rows from source using server-side cursor or keyset pagination |
| `IExecutor.stream_batches()` | Executor | Drive blueprint step loop; yield `BatchMetrics` per batch |
| `IExecutor.on_row_error()` | Executor | Register callback; log `RowErrorLedgerEntry` and continue |
| `ChunkingProceduralBuilder` (SQL) | Compiler | WHILE loop + chunk variables for script-only path (Phase A) |

## Batch loop (Phase C pseudocode)

```text
for blueprint in ordered_blueprints:
    with adapter_factory.create(ref, connection) as adapter:
        for batch in adapter.fetch_batch(source_query, batch_size):
            transform_rows(batch)
            write_to_staging(batch)
            emit BatchMetrics
            on row failure → RowErrorLedgerEntry, continue
    run target INSERT/UPSERT for blueprint
    commit savepoint
```

## Adapter contract

- `fetch_batch` must never accumulate more than `batch_size` rows per yield
- `close()` is always called via context manager (`with adapter:`)
- `health_check()` runs before migration start for connectivity validation

## Error ledger

Row failures produce `RowErrorLedgerEntry` records with:

- `blueprint_sequence`
- `batch_number`
- `row_identity` (primary key or source natural key columns)
- `error_code` and human-readable `message`

The executor aggregates these into `ExecutionReport.row_errors` without aborting
the full migration unless the blueprint policy is `FAIL`.

## Performance notes

- Default `batch_size` should align with blueprint `chunking_strategy.chunk_size` when enabled
- Adapters should prefer keyset pagination (`WHERE id > @last_id`) over `OFFSET` for large tables
- Executor emits structured JSON logs per batch (`rows_processed`, `duration_ms`)
- S3 CSV adapters stream file chunks and parse incrementally; never read full file to RAM

## v1 status

Phase A generates self-contained SQL with WHILE chunking. Phase C stubs
(`StubExecutor`, `StubConnectionAdapter`) reserve interfaces without executing
scripts. No structural refactor is required to add real implementations.
