# Data Migration Engine — End-to-End Requirements Document

**Version:** 1.0.0-draft  
**Status:** For review — implementation to follow step-by-step after approval  
**First target dialect:** MySQL  
**First deliverable:** SQL script generation only (Phase A), architected for full ELT execution (Phase C)  
**Architecture:** See [ARCHITECTURE.md](ARCHITECTURE.md) for implementation-aligned system design, diagrams, and design patterns.  
**Platform integration:** See [../../docs/INTEGRATION.md](../../docs/INTEGRATION.md) for cross-product APIs and contracts.

---

## 1. Executive Summary

Build a **configuration-driven, multi-tenant ELT migration engine** in Python that reads a declarative JSON blueprint and produces a **self-contained, runnable SQL script**. When executed on the target database, that script must connect to all configured sources, transform data through a CTE/procedural pipeline, and load results into target tables — without requiring a separate orchestrator for v1.

The codebase must be **production-grade**, **SOLID-compliant**, **interface-driven**, and **extensible via factories** so that new output formats, target dialects, source adapters, and conflict strategies can be added without rewriting the core.

---

## 2. Goals & Non-Goals

### 2.1 Goals (v1 — Phase A)

| Goal | Description |
|------|-------------|
| Config parsing | Read and validate JSON blueprint → immutable DTO graph |
| Config validation | Fail-fast validator with whitelisted functions/operators |
| SQL compilation | Generate one self-contained MySQL script per migration run |
| CTE pipeline | Staging → pre-filters → joins → derivations → post-filters → target insert |
| Idempotency | Conflict handling driven by `on_conflict` config value |
| Chunking | Single script with parameterized loop / procedural block |
| Transactions | Per blueprint step: savepoint + commit semantics |
| Extensibility | Factories for script generator, dialect, and (future) connection adapters |
| Tests | Unit + golden-file tests; integration tests against MySQL and MS SQL Server |

### 2.2 Non-Goals (v1)

| Non-Goal | Notes |
|----------|-------|
| UI / wizard | Backend first; UI requirements to follow separately |
| Python-side execution engine | v1 outputs SQL only; executor layer stubbed for Phase C |
| Full staging orchestration in Python | v1 embeds source connectivity **inside generated SQL** |
| PostgreSQL dialect implementation | Deferred; MySQL first; dialect factory ready for PG/Oracle later |

### 2.3 Future (Phase C — architect now, implement later)

- Python executor: run generated scripts, stream batches, structured JSON logging
- Connection adapters: pull from S3/MySQL/MSSQL/PG into staging when script-only approach is insufficient
- Row-level error ledger and continue-on-failure
- Optional hybrid: script preamble + Python-side staging for unsupported federated paths

---

## 3. Stakeholder Decisions (Captured Answers)

| # | Topic | Decision |
|---|--------|----------|
| 1 | v1 scope | **A** — SQL generation only; structure must support **C** (full ELT) later |
| 2 | Multi-source handling | Generated SQL is **self-contained**; running it on target must load data from **all sources** referenced in config (connections embedded or established in script preamble) |
| 3 | Factory layers | **IScriptGenerator** (SQL today, interface for future formats) + **IDialect/DialectFactory** (MySQL v1) + **IConnectionAdapter** (reserved for Phase C execution) |
| 4 | First dialect | **MySQL** (not PostgreSQL) |
| 5 | `on_conflict` | Not UPSERT-only; support configurable strategies: **FAIL**, **IGNORE**, **UPSERT**, **IGNORE_AND_LOG**, **IGNORE_AND_INSERT_UNPROCESSED**, extensible registry |
| 6 | Chunking | **One script** with parameterized loop / stored procedure block |
| 7 | Transactions | **Transaction per blueprint step** using **SAVEPOINT** + **COMMIT** per `sequence_order` step |
| 8 | Expression safety | Separate **Config Validator** module; whitelist functions/operators; **fail before compilation** |
| 9 | `derivations.*` references | Compiler resolves to valid MySQL SQL (CTE columns or procedural variables — best approach for runnable output) |
| 10 | `post_filters` | Same treatment as pre-filters; applied after derivations CTE/layer |
| 11 | Code structure | Clean, prod-deployable, intuitive naming; easy onboarding for new developers |
| 12 | Tech stack | **Open source only**; recommended stack in Section 8 |
| 13 | UI | Out of scope for v1; FE requirements later |
| 14 | Testing targets | **MySQL** and **MS SQL Server** (sources and/or integration environments) |
| 15 | Safe casting | Use **dialect-favorable syntax** (MySQL: no `TRY_CAST`; use safe-cast patterns via `BaseDialect`) |

---

## 4. Functional Requirements

### 4.1 Input: Master Migration JSON

Top-level fields (from sample + extensions):

```json
{
  "migration_id": "...",
  "client_id": "...",
  "version": "...",
  "output_format": "SQL",
  "connections": { ... },
  "blueprints": [ ... ]
}
```

> `output_format` is a new top-level field for `ScriptGeneratorFactory` (default: `SQL`).

Each **blueprint** (`sequence_order` ordered):

| Block | Purpose |
|-------|---------|
| `target` | `connection_ref`, `schema`, `table_name`, `primary_keys`, `on_conflict`, optional `unprocessed_table` |
| `sources.root_table` | Root source: `connection_ref`, `schema`/`file_name`, `table_name`, `alias` |
| `sources.joins[]` | Join type, source ref, alias, join `conditions[]` |
| `chunking_strategy` | `is_enabled`, `chunk_by_column`, `chunk_size` |
| `pre_filters[]` | Raw SQL predicates (validated) |
| `derivations[]` | `variable_name`, `expression` (validated) |
| `post_filters[]` | Raw SQL predicates (validated) |
| `mappings[]` | Target column mapping with `source_type`, `source_value`, `cast_to`, `is_nullable` |

**Mapping `source_type` values:** `DIRECT`, `DERIVED`, `EXPRESSION`, `CONSTANT`

### 4.2 Compilation Pipeline (per blueprint)

Strict sequential phases — compiler orchestrates; dialect supplies syntax:

```
1. Source Resolution & Connection Preamble
   └── Embed/create remote access objects (FEDERATED, ODBC, temp staging tables, S3 load steps)

2. Staged Sources CTE
   └── Map each source to a named CTE (alias-scoped)

3. Pre-Filtering CTE
   └── WHERE pre_filters on staged data

4. Relational Assembly CTE
   └── JOIN graph with explicit aliases

5. Derivation / Calculation CTE
   └── Project derivations.variable_name columns

6. Post-Filtering CTE
   └── WHERE post_filters on derived dataset

7. Target Projection & Load
   └── Safe cast via dialect → INSERT with conflict strategy
```

**Rule:** No deep joins or formulas inlined in final INSERT — all logic in CTEs (or procedural equivalents where MySQL CTE limits apply).

> **See Section 4A** for the full CTE-based SQL generation specification (naming, compiler design, and example output).

### 4.3 Self-Contained Multi-Source SQL (Critical)

Because v1 generates scripts only, and sources may differ (MySQL, MSSQL, PostgreSQL, S3 CSV), the generated script must include:

1. **Session setup** — variables for connection params (or references to pre-provisioned linked objects)
2. **Source access bootstrap** — dialect-specific patterns, e.g.:
   - MySQL → MySQL: `FEDERATED` table or `CREATE TEMPORARY TABLE ... SELECT ...` via connection string variables
   - MySQL → MSSQL: ODBC / linked server pattern or `CREATE TEMPORARY TABLE staging_xxx AS ...` via supported bridge
   - MySQL → S3 CSV: `LOAD DATA` / `INTO TABLE` temp staging (or AWS S3 table function if available)
3. **Staging CTEs** reading from bootstrapped temp/staging tables
4. **Target write** to local MySQL target schema

> **Design note:** A `SourceBootstrapCompiler` sub-component (dialect-aware) generates the preamble per `connection.type`. Unsupported combinations fail at validation with a clear error — not at runtime.

### 4.4 Conflict Strategies (`on_conflict`)

Configurable per blueprint target. Strategy registry (extensible):

| Strategy | MySQL behavior (v1) |
|----------|---------------------|
| `FAIL` | Plain `INSERT`; duplicate key raises error → rollback savepoint |
| `IGNORE` | `INSERT IGNORE` |
| `UPSERT` | `INSERT ... ON DUPLICATE KEY UPDATE ...` |
| `IGNORE_AND_LOG` | `INSERT IGNORE` + rows not inserted logged to error/unprocessed audit table |
| `IGNORE_AND_INSERT_UNPROCESSED` | Failed/rejected rows routed to `target.unprocessed_table` (config-driven) |

Each strategy implements `IConflictStrategy` (Strategy pattern); `MySqlDialect` delegates UPSERT syntax generation.

### 4.5 Chunking

When `chunking_strategy.is_enabled = true`:

- Emit **one script** containing a **stored procedure** or **prepared block** that:
  - Declares chunk bounds (`min_id`, `max_id`, `chunk_size`)
  - Loops with `WHILE` / cursor over chunk ranges
  - Applies `chunk_by_column` filter per iteration
  - Uses **SAVEPOINT** per chunk (optional sub-savepoint) within blueprint savepoint
- Chunk variables parameterized at script top for operator override

### 4.6 Transaction & Savepoint Model

For migration with blueprints `[1, 2, 3]`:

```sql
START TRANSACTION;

-- Blueprint sequence_order = 1
SAVEPOINT bp_step_1;
-- ... CTE pipeline + insert ...
RELEASE SAVEPOINT bp_step_1;
COMMIT;

START TRANSACTION;
SAVEPOINT bp_step_2;
...
```

**Requirement:** Each `sequence_order` step is independently committable; failure in step N does not undo committed steps 1..N-1 unless explicitly wrapped in outer transaction (default: **commit per step**).

### 4.7 Config Validation (Fail-Fast)

Separate module: `validators/` — runs **before** compiler.

| Validation | Rule |
|------------|------|
| Schema | Required fields, types, referential integrity (`connection_ref` exists) |
| SQL expressions | Whitelist functions (`COALESCE`, `CONCAT`, `REGEXP_REPLACE`, `CASE`, etc.) |
| Operators | `=`, `<>`, `<`, `>`, `<=`, `>=`, `IN`, `LIKE`, `AND`, `OR` |
| Join conditions | Both sides reference known aliases |
| Mappings | `cast_to` types allowed for target dialect |
| Source connectivity | Each `connection.type` + target dialect combo must be supported |
| Derivation refs | `derivations.xxx` in mappings must match declared `variable_name` |
| Primary keys | Non-empty for UPSERT / IGNORE_AND_* strategies |

Validation errors → structured report (JSON-serializable); **no SQL generated**.

### 4.8 Derivation Reference Resolution

**Approach:** Compiler builds a `calculation_layer` CTE (or equivalent temp result) exposing derivation columns by `variable_name`. Mappings with `source_type: DERIVED` and `source_value: derivations.formatted_phone` resolve to `calculation_layer.formatted_phone` in generated SQL.

`EXPRESSION` mappings pass through validated expressions in projection layer.  
`CONSTANT` mappings emit literal values with safe cast.

### 4.9 Post-Filters

Applied as a dedicated CTE (`filtered_results`) after derivations:

```sql
filtered_results AS (
  SELECT * FROM calculation_layer
  WHERE <post_filter_1> AND <post_filter_2> ...
)
```

Empty `post_filters` → pass-through CTE or skip (compiler optimization).

### 4.10 Safe Casting (MySQL v1)

`BaseDialect` methods:

- `safe_cast(expression, target_type) -> str`
- MySQL examples:
  - UUID/string: `NULLIF(TRIM(expr), '')` + validation
  - Numeric: `CAST(expr AS DECIMAL(12,4))` with `CASE WHEN expr REGEXP '^[0-9.]+$' ...`
  - Date: `STR_TO_DATE` with format guard
- No raw `TRY_CAST` in output — dialect owns all cast semantics

---

## 4A. CTE-Based SQL Script Generation (Design Specification)

This section defines **how** the SQL compiler produces scripts. Every blueprint compiles to a **linear chain of named CTEs** — one responsibility per CTE — followed by a thin `INSERT` that only reads from the final projection CTE.

### 4A.1 Why CTEs

| Benefit | How it helps |
|---------|----------------|
| **Readability** | Each config block maps to one visible SQL block; DBAs can debug step-by-step |
| **SRP in SQL** | Staging, filtering, joins, derivations, and load are never mixed |
| **Testability** | Golden tests can assert individual CTE fragments |
| **Idempotency isolation** | Conflict logic stays only in the final `INSERT`; transforms are pure `SELECT` |
| **Dialect portability** | CTE syntax is standard; only casts/UPSERT differ per `BaseDialect` |

### 4A.2 CTE Pipeline — Config Block to CTE Mapping

Each blueprint (`sequence_order = N`) produces one `WITH` chain. CTE names are **deterministic** (derived from alias + stage), never user-supplied.

| Order | Config block | CTE name pattern | Responsibility |
|-------|--------------|------------------|----------------|
| 0 | *(preamble)* | `stg_{alias}` | One CTE per source alias reading from bootstrap temp/federated table |
| 1 | `pre_filters` | `pre_filtered_{root_alias}` | `SELECT * FROM stg_{root} WHERE <pre_filters>` |
| 2 | `sources.joins` | `joined_{root_alias}` | Join `pre_filtered_*` with `stg_*` tables per join graph |
| 3 | `derivations` | `calculation_layer` | `SELECT joined.*, <derivation_exprs> FROM joined_*` |
| 4 | `post_filters` | `filtered_results` | `SELECT * FROM calculation_layer WHERE <post_filters>` *(skipped if empty)* |
| 5 | `mappings` | `target_projection` | Project + `safe_cast` every `target_column` |
| 6 | `target` | *(no CTE)* | `INSERT INTO schema.table SELECT * FROM target_projection` + conflict clause |

**Naming rules:**

- Source staging: `stg_cm`, `stg_gam`, `stg_tih` (alias from config)
- Never reuse CTE names across blueprints (prefix with `bp{N}_` when emitted in one script: `bp1_stg_cm`)
- `calculation_layer` and `target_projection` are fixed logical names (prefixed per blueprint)

### 4A.3 Generated Script Anatomy (Full Blueprint)

```sql
-- ============================================================
-- Migration: mig_multi_server_enterprise_2026
-- Blueprint: sequence_order = 1 → core.customers
-- ============================================================

START TRANSACTION;
SAVEPOINT bp_step_1;

-- [PREAMBLE] Source bootstrap (SourceBootstrapCompiler)
-- Creates temp/federated access for remote sources
CREATE TEMPORARY TABLE IF NOT EXISTS _bootstrap_cm AS
  SELECT * FROM federated_crm.customer_master;   -- client_crm_mysql

CREATE TEMPORARY TABLE IF NOT EXISTS _bootstrap_gam AS
  SELECT * FROM staging_csv.geo_address_mapping; -- client_archival_s3

-- [CTE PIPELINE] (CtePipelineBuilder)
WITH
  bp1_stg_cm AS (
    SELECT * FROM _bootstrap_cm
  ),
  bp1_stg_gam AS (
    SELECT * FROM _bootstrap_gam
  ),
  bp1_pre_filtered_cm AS (
    SELECT * FROM bp1_stg_cm AS cm
    WHERE cm.status = 'ACTIVE'
  ),
  bp1_joined_cm AS (
    SELECT cm.*, gam.*
    FROM bp1_pre_filtered_cm AS cm
    LEFT JOIN bp1_stg_gam AS gam
      ON gam.legacy_cust_id = cm.id
  ),
  bp1_calculation_layer AS (
    SELECT
      joined.*,
      REGEXP_REPLACE(cm.phone_raw, '[^0-9+]', '') AS formatted_phone
    FROM bp1_joined_cm AS joined
  ),
  bp1_target_projection AS (
    SELECT
      <dialect.safe_cast(cm.global_uuid, 'UUID')>       AS id,
      <dialect.safe_cast(cm.company_legal_name, 'VARCHAR(255)')> AS company_name,
      <dialect.safe_cast(formatted_phone, 'VARCHAR(32)')> AS phone,
      <dialect.safe_cast(COALESCE(gam.country_code, 'USA'), 'VARCHAR(3)')> AS country_iso
    FROM bp1_calculation_layer
  )
INSERT INTO core.customers (id, company_name, phone, country_iso)
SELECT id, company_name, phone, country_iso
FROM bp1_target_projection
ON DUPLICATE KEY UPDATE
  company_name = VALUES(company_name),
  phone        = VALUES(phone),
  country_iso  = VALUES(country_iso);

RELEASE SAVEPOINT bp_step_1;
COMMIT;
```

**Hard rules enforced by compiler:**

1. Final `INSERT` / `INSERT IGNORE` / `ON DUPLICATE KEY UPDATE` references **only** `target_projection`
2. Join conditions, derivations, and mapping expressions **never** appear inside the `INSERT` clause
3. `calculation_layer` exposes every `derivations.variable_name` as a column
4. `DERIVED` mappings resolve `derivations.xxx` → `calculation_layer.xxx`
5. `DIRECT` / `EXPRESSION` mappings reference aliased columns from the join layer

### 4A.4 Compiler Module Design (`CtePipelineBuilder`)

Python builds the CTE chain as a list of immutable stage objects — no string concatenation scattered across the codebase.

```python
@dataclass(frozen=True)
class CteStage:
    name: str
    body: str          # SELECT ... (no trailing comma)
    comment: str = ""  # optional config comment for generated SQL

class CtePipelineBuilder:
    def build(self, blueprint: BlueprintDTO, dialect: BaseDialect) -> CtePipeline:
        stages: list[CteStage] = []
        stages.extend(self._build_source_stages(blueprint))
        stages.append(self._build_pre_filter_stage(blueprint))
        stages.append(self._build_join_stage(blueprint))
        stages.append(self._build_derivation_stage(blueprint))
        if blueprint.post_filters:
            stages.append(self._build_post_filter_stage(blueprint))
        stages.append(self._build_projection_stage(blueprint, dialect))
        return CtePipeline(stages=stages)

class CtePipeline:
    def render_with_clause(self) -> str:
        """Emit: WITH cte1 AS (...), cte2 AS (...)"""
```

**One builder method per config block** — mirrors SRP:

| Builder method | Config input |
|----------------|--------------|
| `_build_source_stages` | `sources.root_table`, `sources.joins[]` |
| `_build_pre_filter_stage` | `pre_filters[]` |
| `_build_join_stage` | `sources.joins[]` |
| `_build_derivation_stage` | `derivations[]` |
| `_build_post_filter_stage` | `post_filters[]` |
| `_build_projection_stage` | `mappings[]` + `dialect.safe_cast()` |

`MigrationCompiler` orchestrates: preamble → `CtePipelineBuilder` → `ConflictStrategyFactory` → `TransactionBuilder`.

### 4A.5 Chunking + CTE (Procedural Wrapper)

When `chunking_strategy.is_enabled = true`, the **same CTE pipeline** is wrapped inside a loop. The chunk predicate is injected into `pre_filtered_*` (or a dedicated `chunk_filtered` CTE):

```sql
SET @chunk_min = 0;
SET @chunk_size = 25000;

WHILE @chunk_min IS NOT NULL DO
  SAVEPOINT bp2_chunk;

  WITH
    bp2_chunk_filtered AS (
      SELECT * FROM bp2_stg_tih
      WHERE tih.id > @chunk_min AND tih.id <= @chunk_min + @chunk_size
    ),
    bp2_pre_filtered_tih AS (
      SELECT * FROM bp2_chunk_filtered AS tih
      WHERE tih.invoice_date >= '2022-01-01'
    ),
    -- ... remaining CTE chain unchanged ...
    bp2_target_projection AS ( ... )
  INSERT INTO billing.billing_details (...)
  SELECT ... FROM bp2_target_projection
  ON DUPLICATE KEY UPDATE ...;

  SET @chunk_min = @chunk_min + @chunk_size;
  RELEASE SAVEPOINT bp2_chunk;
END WHILE;
```

Chunking logic lives in `ChunkingProceduralBuilder`; it does **not** duplicate the CTE pipeline — it injects a chunk filter stage at the head.

### 4A.6 Multi-Blueprint Script Layout

A full migration script is a **sequence of independent blueprint blocks**, each with its own transaction + savepoint:

```
[Script Header — migration_id, client_id, generated timestamp]
[Connection Variables — parameterized @host, @user, etc.]

── Blueprint 1 ──
  PREAMBLE → WITH ... → INSERT → COMMIT

── Blueprint 2 ──
  PREAMBLE → PROCEDURE/WHILE chunk loop → WITH ... → INSERT → COMMIT

── Blueprint 3 ──
  PREAMBLE → WITH ... → INSERT → COMMIT
```

Blueprints 2 and 3 in the sample both target `billing.billing_details` — each produces its own CTE chain and UPSERT; no shared CTEs across blueprints.

### 4A.7 MySQL Dialect Notes (Target v1)

| Topic | Approach |
|-------|----------|
| CTE support | MySQL 8.0+ (`WITH` required); document minimum version |
| `REGEXP_REPLACE` | Available MySQL 8.0+; map in `MySqlDialect` |
| Multiple CTEs | Standard comma-separated `WITH` chain |
| CTE + INSERT | Single statement: `WITH ... INSERT INTO ... SELECT ...` |
| Temp tables in preamble | `CREATE TEMPORARY TABLE` for cross-connection staging before `WITH` |
| UUID cast | `dialect.safe_cast()` — no `TRY_CAST` |

If a future MySQL version or mode lacks CTE support, `CtePipeline.render_as_temp_tables()` is the fallback (CREATE TEMPORARY TABLE per stage) — interface reserved, not v1.

### 4A.8 What Never Goes in the Final INSERT

| Forbidden in INSERT | Belongs in |
|---------------------|------------|
| `JOIN` clauses | `joined_*` CTE |
| `CASE WHEN` / `COALESCE` for transforms | `calculation_layer` or `target_projection` |
| `WHERE` filters | `pre_filtered_*` or `filtered_results` |
| `REGEXP_REPLACE`, `CONCAT` derivations | `calculation_layer` |
| Safe cast expressions | `target_projection` only |
| Raw source table references | `stg_*` CTE (via bootstrap tables) |

The `INSERT` statement contains **only**: target table name, column list, `SELECT` from `target_projection`, and conflict strategy clause.

### 4A.9 Golden-File Testing for CTE Output

Tests normalize whitespace and compare:

1. **Full script** — `tests/golden/expected/sample_migration.sql`
2. **Per-blueprint CTE fragment** — `tests/golden/expected/bp1_cte_pipeline.sql`
3. **Per-stage unit tests** — assert single `CteStage.render()` output

Any config change that alters CTE structure must update golden files explicitly in the PR.

---

## 5. Architecture & Design Patterns

### 5.1 Component Diagram

```
┌─────────────────────┐
│  Migration JSON     │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  Config Validator   │  ← fail fast, whitelist
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  Blueprint Parser   │  → immutable DTOs (MasterMigrationBlueprint)
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ ScriptGeneratorFactory │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│ SqlScriptGenerator  │  ← orchestrates compilation
└──────────┬──────────┘
           ├──► MigrationCompiler (per blueprint)
           │         ├── SourceBootstrapCompiler
           │         ├── CtePipelineBuilder
           │         ├── ChunkingProceduralBuilder
           │         └── TransactionSavepointBuilder
           ▼
┌─────────────────────┐
│   DialectFactory    │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│    MySqlDialect     │  ← casts, UPSERT, concat, regexp, savepoints
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  ConflictStrategy   │  ← per on_conflict value
│      Registry       │
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│  Final .sql script  │
└─────────────────────┘

[Phase C — reserved]
┌─────────────────────┐
│ ConnectionAdapter   │
│      Factory        │  → MySQL, MSSQL, PG, S3 adapters
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│     Executor        │  → streaming, logging, error ledger
└─────────────────────┘
```

### 5.2 Factory & Interface Contracts

#### Script Generator Factory

```python
class IScriptGenerator(ABC):
    def generate(self, blueprint: MasterMigrationBlueprint) -> GeneratedScript: ...

class ScriptGeneratorFactory:
    @staticmethod
    def create(output_format: str) -> IScriptGenerator: ...
    # "SQL" → SqlScriptGenerator (v1 only registered)
```

#### Dialect Factory

```python
class BaseDialect(ABC):
    def safe_cast(self, expr: str, data_type: str) -> str: ...
    def upsert_clause(self, table: str, pk_cols: list[str], update_cols: list[str]) -> str: ...
    def begin_transaction(self) -> str: ...
    def savepoint(self, name: str) -> str: ...
    def commit(self) -> str: ...
    # ... pure string formatting, stateless

class DialectFactory:
    @staticmethod
    def create(dialect_type: str) -> BaseDialect: ...
    # "MYSQL" → MySqlDialect (v1)
    # "POSTGRESQL", "ORACLE" → future
```

#### Conflict Strategy Registry

```python
class IConflictStrategy(ABC):
    def build_insert_statement(self, ctx: InsertContext) -> str: ...

class ConflictStrategyFactory:
    @staticmethod
    def create(strategy: str, dialect: BaseDialect) -> IConflictStrategy: ...
```

#### Connection Adapter Factory (Phase C — interface only in v1)

```python
class IConnectionAdapter(ABC):
    def connect(self) -> None: ...
    def fetch_batch(self, query: str, batch_size: int) -> Iterator[Row]: ...
    def close(self) -> None: ...
```

### 5.3 SOLID / SRP Module Boundaries

| Module | Responsibility | Must NOT |
|--------|----------------|----------|
| `models/` | Frozen DTOs, enums | SQL, I/O |
| `parsers/` | JSON → DTOs | Validation rules, SQL |
| `validators/` | Config + expression whitelist | SQL generation |
| `dialects/` | Dialect string formatting | Read files, orchestration |
| `compilers/` | Pipeline orchestration | Hardcoded MySQL keywords |
| `generators/` | Script assembly, file output | Parse JSON |
| `factories/` | Registry / creation | Business logic |
| `strategies/conflict/` | Insert/conflict variants | CTE building |
| `adapters/` (stub) | DB/file connections | SQL compilation |
| `executor/` (stub) | Run scripts, telemetry | Parse config |
| `logging/` | Structured JSON logger setup | Domain logic |

---

## 6. Project Structure (Production Layout)

> Platform layout: see [INTEGRATION.md](../../docs/INTEGRATION.md). This product lives under `script-generator/`.

```
DataMigrationTool/
├── docs/
│   ├── INTEGRATION.md
│   └── sampleConfigfile.json
├── script-generator/
│   ├── pyproject.toml
│   ├── README.md
│   ├── docs/
│   │   ├── REQUIREMENTS.md
│   │   └── ARCHITECTURE.md
│   ├── config/
│   │   └── whitelists/
│   ├── src/
│   │   └── migration_engine/
│   │       ├── __main__.py              ← CLI entry: parse → validate → generate
│   │       ├── models/
│   │       ├── parsers/
│   │       ├── validators/
│   │       ├── dialects/
│   │       ├── strategies/conflict/
│   │       ├── compilers/
│   │       ├── generators/
│   │       ├── factories/
│   │       ├── adapters/                # Phase C — stubs
│   │       ├── executor/                # Phase C — stubs (migrator will own execution)
│   │       └── logging/
│   └── tests/
│       ├── unit/
│       ├── golden/expected/
│       └── integration/
├── config-platform/                     # Planned — UI + API
└── migrator/                            # Planned — script execution
```

---

## 7. Recommended Tech Stack (Open Source)

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | **Python 3.11+** | Team familiarity, rich ecosystem |
| DTOs / parsing | **Pydantic v2** | Immutable models, validation hooks, JSON schema export |
| JSON Schema | **pydantic + optional jsonschema** | Align with `$schema` in config |
| Logging | **structlog** | Native structured JSON logs for Phase C |
| CLI | **typer** | Clean CLI for `generate`, future `execute` |
| Testing | **pytest** + **pytest-cov** | Standard, fixtures |
| Integration DB | **testcontainers-python** | Spin MySQL + MSSQL for CI |
| SQL diff (golden) | **pytest** + normalized string compare | Golden-file regression |
| Lint / format | **ruff** | Fast, replaces flake8+isort |
| Type checking | **mypy** (optional strict) | Prod quality |
| Packaging | **uv** or **poetry** | Reproducible deps |
| Config whitelist | **YAML** files in repo | Easy to extend without code changes |

**No proprietary or paid libraries.**

---

## 8. CLI Behavior (v1)

```bash
migration-engine validate --config sampleConfigfile.json
migration-engine generate --config sampleConfigfile.json --output output/migration.sql
migration-engine generate --config sampleConfigfile.json --dialect MYSQL
```

Exit codes: `0` success, `1` validation failure, `2` compilation failure.

---

## 9. Implementation Phases (Step-by-Step Plan)

**Status legend:** `[x]` = complete · `[ ]` = not started / in progress

### Phase 0 — Foundation

- [x] Scaffold project (`pyproject.toml`, folder structure, ruff, pytest)
- [x] Define enums: `ConnectionType`, `SourceType`, `ConflictStrategy`, `OutputFormat`
- [x] Define frozen DTOs (`MasterMigrationBlueprint` and nested models)
- [x] Define ABCs: `BaseDialect`, `IScriptGenerator`, `IConflictStrategy`, `IConnectionAdapter` (stub)
- [x] Implement factories (empty registries with MySQL/SQL only)
- [x] Structured logger setup (minimal)

**Exit criteria:** `pip install -e .` works; empty tests pass; factories return typed stubs.

### Phase 1 — Parser + Validator

- [x] `BlueprintParser`: JSON file → `MasterMigrationBlueprint`
- [x] `SchemaValidator`: required fields, refs, sequence_order uniqueness
- [x] `ExpressionValidator`: whitelist functions/operators from YAML
- [x] `ConnectivityValidator`: source type × target dialect support matrix
- [x] CLI `validate` command
- [x] Unit tests for valid/invalid configs

**Exit criteria:** `sampleConfigfile.json` validates cleanly; intentional bad configs fail with clear errors.

### Phase 2 — MySQL Dialect + Conflict Strategies

- [x] `MySqlDialect`: safe_cast, concat, regexp, transaction/savepoint keywords
- [x] All conflict strategy implementations for MySQL
- [x] Unit tests per strategy and cast helper

**Exit criteria:** Dialect and strategies tested in isolation (no full compiler yet).

### Phase 3 — CTE Pipeline Compiler

> Implements **Section 4A** (`CtePipelineBuilder`, `CteStage`, deterministic CTE naming).

- [x] `CtePipelineBuilder`: pre-filters → joins → derivations → post-filters → projection
- [x] Derivation reference resolution (`derivations.xxx`)
- [x] Mapping projection with safe casts
- [x] Unit tests per pipeline stage

**Exit criteria:** Single-blueprint, single-source SQL fragment matches golden snippets.

### Phase 4 — Source Bootstrap + Multi-Source

- [x] `SourceBootstrapCompiler`: preamble for MySQL, MSSQL, PG, S3 CSV sources
- [x] Document supported connection patterns per source type
- [x] Integration tests: generated script runs against MySQL target with MSSQL/MySQL sources

**Exit criteria:** Blueprint 1 and 2 from sample config produce runnable scripts.

### Phase 5 — Chunking + Transactions

- [x] `ChunkingProceduralBuilder`: WHILE loop + chunk variables
- [x] `TransactionBuilder`: SAVEPOINT per blueprint step, COMMIT per step
- [x] Multi-blueprint orchestration in `MigrationCompiler`
- [x] Golden-file test: full `sampleConfigfile.json` → expected SQL

**Exit criteria:** Full sample config generates one `.sql` file; manual run loads data on MySQL target.

### Phase 6 — SqlScriptGenerator + CLI

- [x] Wire `SqlScriptGenerator` through factories
- [x] CLI `generate` command
- [x] README with usage examples

**Exit criteria:** End-to-end Phase A complete; reviewer can run validate + generate.

### Phase 7 — Hardening & Phase C Stubs

- [x] Stub `adapters/` and `executor/` with interfaces + docstrings
- [x] Expand integration test matrix (MySQL + MSSQL)
- [x] Performance notes: streaming hooks documented for executor
- [x] Error message polish; validation report JSON export

**Exit criteria:** Codebase ready for Phase C without structural refactor.

### Phase 8 — Future (Phase C — when requested)

- [ ] Connection adapter implementations
- [ ] Executor with batch streaming, row-level error ledger
- [ ] Optional Python-side staging fallback
- [ ] Additional dialects (PostgreSQL, Oracle) via `DialectFactory.register()`
- [ ] UI integration API endpoints

---

## 10. Testing Strategy

| Level | Scope |
|-------|-------|
| Unit | Parser, validators, dialect, each compiler builder, each conflict strategy |
| Golden | Full SQL output vs committed `tests/golden/expected/*.sql` (normalized whitespace) |
| Integration | Run generated script on MySQL target; sources on MySQL + MSSQL testcontainers |
| Regression | Any config/schema change updates golden files explicitly in PR |

**Test environments:** MySQL 8.x (target), MS SQL Server 2019+ (source), optional MySQL as secondary source.

---

## 11. Open Items / Assumptions to Confirm on Review

1. **S3 in MySQL scripts:** Confirm acceptable approach (`LOAD DATA LOCAL INFILE` from pre-downloaded path vs `S3` table engine / external tool preamble). May require ops to stage files before script run unless AWS integration is added to script preamble.
2. **MSSQL → MySQL live link:** Confirm ODBC/linked-server availability in deployment environment, or accept temp-table + manual pre-export for unsupported paths in v1.
3. **`on_conflict` enum final list:** Confirm exact string values for config (e.g. `IGNORE_AND_LOG` vs `IGNORE_AND_LOG_TO_TABLE`).
4. **`unprocessed_table` schema:** Is it always in target schema? Same connection as target?
5. **Credentials in generated SQL:** Should connection strings be parameterized (`@host`, `@user`) vs embedded from config (security review needed)?
6. **Blueprint 3 (UNION scenario):** Sample appends to same target table — confirm UPSERT handles archive + live dedup correctly.

---

## 12. Success Criteria (v1 Sign-Off)

**Status legend:** `[x]` = complete · `[ ]` = not started / in progress

- [x] `validate` catches all invalid configs before generation
- [x] `generate` produces one runnable MySQL script from `sampleConfigfile.json`
- [x] Script includes source bootstrap, CTE pipeline, chunking loop (blueprint 2), savepoints per step
- [x] All `on_conflict` strategies implemented and tested
- [x] Factories allow registering new dialect/output format without changing compiler core
- [x] Adapters/executor stubs present for Phase C
- [x] Golden + integration tests pass on MySQL and MSSQL
- [x] Code structure matches Section 6; passes ruff; documented README

---

## 13. Next Steps

1. Review this document — especially Section 11 open items.
2. Reply with approvals, corrections, or answers to open items.
3. When ready to implement, ask: *"Refer to REQUIREMENTS.md — start Phase 0."*
