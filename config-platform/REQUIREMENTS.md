# Config Platform — Requirements (v1)

**Status:** Spec complete (§12 OQ-1–22 closed). **Progress:** §11 checklists (`[x]` / `[ ]`). P0–P2 and P1.1–P1.6 done; P3 next.  
**Product:** `config-platform/` (UI + API)  
**Based on:** Original UI toolkit ideas (refined and aligned with script-generator contract)  
**Related:** [../docs/INTEGRATION.md](../docs/INTEGRATION.md) · [../docs/sampleConfigfile.json](../docs/sampleConfigfile.json) · [../script-generator/docs/REQUIREMENTS.md](../script-generator/docs/REQUIREMENTS.md)

---

## 1. Purpose & boundaries

### 1.1 What this product does

| Aspect | Description |
|--------|-------------|
| **Input** | User input via UI (connections, blueprints, mappings, expressions) |
| **Output** | Migration **config JSON** file matching the shared contract |
| **v1 primary deliverable** | **Download JSON** (validated before export) |

### 1.2 What this product does NOT do (v1)

| Responsibility | Owner |
|----------------|--------|
| Compile config → SQL | **script-generator** (future: API proxy from config API) |
| Execute SQL on target | **migrator** (including user-supplied `.sql` files) |
| Post-migration checksum / audit | **migrator** (future Validation module) |

Config platform **authors** the contract. Other products **consume** it.

### 1.3 Stakeholder decisions (captured)

| Topic | Decision |
|-------|----------|
| Secrets in exported JSON | **Yes for now**; Key Vault integration before production |
| v1 navigation | **Connect + Configs** active; Run / Studio / Validation **Coming soon** (routes exist, no rewrite later) |
| Compile dialect | **MySQL only** for now |
| Schema introspection | **Required** for v1 (target + sources) |
| `on_conflict` strategies | **All 5** engine strategies in v1 |
| `fallback_value` on mappings | **Omitted** until engine supports it |
| `unprocessed_table` | **Yes** when `IGNORE_AND_INSERT_UNPROCESSED`; option to create table on target (copy schema) |
| Custom user `.sql` | **Not part of config JSON** — migrator feature (run generated or upload own script) |
| Auto GROUP BY | **Not in v1**; shell/schema must allow adding later with minimal UI change |
| Test connection | **Required** before Save |
| v1 export | **Download JSON** (validate before download; generate SQL deferred) |
| Download if invalid | **Blocked** until full validation passes (OQ-1) |
| Draft storage | **User choice:** server-side and/or browser local (OQ-3) |
| UI library | **MUI + MUI X Data Grid** (OQ-4, confirmed) — see [§12.1](#121-ui-library-oq-4) |
| Blueprint step layout | **Sidebar** (Layout B) — OQ-5 confirmed after P0 review |
| Duplicate blueprint | **Full deep copy** (OQ-6) |
| S3 introspection | **File listing required**; S3 column header preview optional (OQ-7); **`LOCAL_CSV` column preview required** (§7.1.4) |
| CSV file sources (local / upload) | **Three ingestion modes** with size policy; sample-only introspection (§7.1, OQ-11–14) |
| Connection connectors | **Factory + adapter**; **tiered auth** P1.1–P1.7+ (§7.2, OQ-15–22) |
| Key Vault prep | **Optional `secret_ref`** on API model; export uses `connection_string` until vault (OQ-9) |
| Auth / login | **Deferred** — far future (OQ-10) |
| Frontend stack | **React + TypeScript** + **MUI** |
| Backend stack | **FastAPI** (Python) |
| Deployment model | **Web-first** (hosted or local stack); desktop wrapper optional later — [§1.4](#14-deployment--portability) |

### 1.4 Deployment & portability

**Decision:** Ship config platform as a **browser web app** in v1. Execution-side desktop needs belong primarily to **migrator**, not this product.

#### v1 delivery

| Layer | How it runs | User access |
|-------|-------------|-------------|
| **Web UI** | React SPA (`config-platform/web/`) | Browser |
| **Config API** | FastAPI (`config-platform/api/`) | HTTP from UI only |
| **Hosting** | Internal server/VPC **or** local stack (`localhost`) | IT choice per environment |

The UI **never** connects to databases directly. Introspection and test-connection run on the API host — same pattern whether that host is a shared server or the architect’s laptop.

```text
Architect (browser)  →  Config API  →  source/target DBs (metadata only)
                              ↓
                        export config.json
```

#### Platform split (design vs run)

| Product | v1 delivery | Desktop pressure |
|---------|-------------|------------------|
| **Config platform** | Web app | Low — authoring, validation, export |
| **Script generator** | CLI + HTTP API | Low — automatable compile step |
| **Migrator** | TBD (CLI first) | **High** — run on approved execution host |

Job Runner / Run nav in this UI remains a **placeholder** that deep-links to migrator later; do not merge execution into the config web app.

#### Path to desktop later (if needed)

Not planned for v1. If DBs are only reachable from a laptop/jump box, prefer these paths **in order**:

1. **Local web stack** — start API locally, open browser to `http://127.0.0.1:8000` (minimal extra work; ~same codebase).
2. **Desktop shell** — Electron/Tauri wrapping the same React app + bundled/local FastAPI (~weeks, **high UI reuse**).
3. **Native desktop UI rewrite** — only if compliance blocks Chromium/Electron (**months**; avoid unless required).

**Revision policy:** Web-first does not lock out desktop. Portability depends on keeping the React app a **thin client** of the config API (see §10).

#### Implementation guardrails (P0+)

| Rule | Why |
|------|-----|
| All data and introspection via **config API** | API can move from cloud to laptop without UI rewrite |
| **Single API client module**; base URL from env (`VITE_API_URL`) | Flip hosted vs local in one place |
| **No business logic** that only exists in React | Avoid duplicating rules on desktop |
| Export/validate through API endpoints | Same contracts in browser and desktop shell |
| Draft storage: server **and** local (OQ-3) | Desktop can default to local SQLite/file |

---

## 2. Concepts you need: migration vs blueprint

### 2.1 One migration, many blueprints

A single exported JSON file describes **one migration project** with **one or more blueprint steps**.

Reference: [sampleConfigfile.json](../docs/sampleConfigfile.json)

| Blueprint | `sequence_order` | What it does |
|-----------|------------------|--------------|
| 1 | 1 | MySQL CRM + S3 CSV → `core.customers` |
| 2 | 2 | MSSQL + PostgreSQL → `billing.billing_details` (with chunking) |
| 3 | 3 | S3 archive → **same** `billing.billing_details` (append/UPSERT) |

**Why this matters for the UI:** The wizard is not “one walkthrough = one file.” Users work on a **migration project** that contains a **list of blueprints**. Each blueprint has its own sources, target, mappings, filters, and chunking.

**v1 recommendation:** Support **multiple blueprints per migration** from day one (add / duplicate / reorder / delete). Hiding this behind “one blueprint only” would block real configs like the sample.

### 2.2 Top-level migration fields

Every export must include:

```json
{
  "migration_id": "...",
  "client_id": "...",
  "version": "1.0.0",
  "output_format": "SQL",
  "connections": { },
  "blueprints": [ ]
}
```

These are **migration-level**, not per-blueprint.

---

## 3. Job Runner vs config platform (elaboration)

You asked for context on *“Should Job Runner live in migrator only?”*

### 3.1 Three different user actions

| User action | Product | v1 |
|-------------|---------|-----|
| Build migration **config** | **config-platform** | Yes |
| **Generate** `.sql` from config | **script-generator** | Later (API); not v1 export goal |
| **Run** `.sql` on target (generated or uploaded) | **migrator** | Future |

**Job Runner** = running and monitoring migration execution (logs, progress, errors). That is **migrator** work, not config authoring.

### 3.2 What config UI should do (v1 vs later)

**v1**

- Nav item **Run** visible but **Coming soon** (placeholder view, same shell).
- No embedded streaming terminal in config-platform.

**Later (no shell rewrite)**

- After user validates config and (optionally) generates SQL elsewhere, show **“Open in Migrator”**:
  - Pass migration id + path to SQL artifact (or let migrator pull from API).
- Optional deep link: `MIGRATOR_URL/run?migration_id=...`

**Custom `.sql` (your clarification)**

- User uploads or pastes their **own** SQL in **migrator**, not in the config wizard.
- Unrelated to blueprint JSON. Do **not** add “override JSON with custom script” to Step 5.

```text
config-platform     →  export config.json
script-generator    →  config.json → migration.sql
migrator            →  migration.sql OR user-uploaded.sql → execute on target
```

---

## 4. Application shell (open-closed for future nav)

Persistent left navigation. v1 implements two modules; others are routed placeholders.

```text
┌────────────────────────────────────────────────────────────────────────┐
│  Migration Toolkit                                                     │
├──────────────┬─────────────────────────────────────────────────────────┤
│ 🌐 Connect   │  Workspace (Configs active in v1)                       │
│   [v1]       │                                                         │
│ 🔮 Configs   │  Migration header + blueprint tabs + step wizard        │
│   [v1]       │                                                         │
│ 🚀 Run       │  Coming soon → will link to migrator                    │
│ 🖥️ Studio    │  Coming soon                                            │
│ 📊 Validate   │  Coming soon → post-run audits in migrator               │
└──────────────┴─────────────────────────────────────────────────────────┘
```

**Rule:** Register all nav routes and view slots in v1. Future features add **new views** only — no layout rewrite.

| Module | Route (example) | v1 |
|--------|-----------------|-----|
| Connections Manager | `/connections` | Active |
| Config Spec Builder | `/migrations`, `/migrations/:id` | Active |
| Job Runner | `/run` | Placeholder |
| Database Studio | `/studio` | Placeholder |
| Validation Engine | `/validation` | Placeholder |

---

## 5. Config Spec Builder — wizard structure (revised)

### 5.1 Two-level navigation

1. **Migration level** — identity + connections + blueprint list  
2. **Blueprint level** — per-blueprint wizard steps (repeat for each blueprint)

### 5.2 Migration-level steps

#### Step M0 — Migration identity (project dashboard)

| Field | Required | Notes |
|-------|----------|-------|
| `migration_id` | Yes | Unique slug |
| `client_id` | Yes | Tenant / client |
| `version` | Yes | Semver string, e.g. `1.0.0` |
| `output_format` | Yes | Fixed `SQL` in v1 (read-only) |
| Compile dialect | Display only | **MySQL** in v1 |

**Recommendation:** M0 is the first screen when creating a migration, editable later from migration settings.

#### Step M1 — Connections (also available via 🌐 Connect nav)

Same behaviour as original Step 1 workflow:

- **Database connectors:** selected via `connector_id` — see §7.2 (Phase 1: `mssql_onprem`, `azure_sql_database`, `mysql`, `postgresql`)
- **File connectors:** `local_csv`, `csv_s3_bucket` — §7.1, §7.2.7–§7.2.8
- Dynamic **connector-specific forms** (not one generic host/user/password form)
- **Test / verify required** before Save
- Saved entries populate top-level `connections` map

See [§7 Connection storage](#7-connection-storage-recommendation), [§7.1 File sources](#71-file-sources-csv-extracts), and [§7.2 Connection connectors](#72-connection-connectors--authentication).

#### Step M1b — File sources (CSV extracts) — UX grouping under Connect

Same **Connect** nav as M1; labeled **File sources** in the UI for clarity. Not a separate migration wizard step.

- **Three ingestion modes** (§7.1): local/server path, S3 (existing `CSV_S3_BUCKET`), optional platform upload (size-capped)
- UI guides users away from browser upload when file is large
- **Sample-only introspection** — column names for mapping grid; never loads full file in API
- Blueprint B1 picks `connection_ref` + `file_name` (unchanged contract shape for file-backed sources)

**Deferred:** `LOCAL_XLSX` — sheet selection and run-time conversion; separate phase after CSV (OQ-14).

#### Step M2 — Blueprint list

- List blueprints with `sequence_order`
- Actions: Add, Duplicate, Delete, Reorder (drag or up/down)
- Select a blueprint → enter blueprint wizard (§5.3)

### 5.3 Per-blueprint wizard steps

| Step | Name | Maps to JSON |
|------|------|----------------|
| B1 | Sources & joins | `sources.root_table`, `sources.joins[]` |
| B2 | Target & conflict | `target.*` |
| B3 | Mappings & derivations | `derivations[]`, `mappings[]` |
| B4 | Filters & chunking | `pre_filters`, `post_filters`, `chunking_strategy` |
| B5 | Review (blueprint) | Read-only summary + blueprint-level checks |

**Removed from original spec**

- ~~Custom script override in wizard~~ → migrator only  
- ~~`fallback_value`~~ → not in engine schema  
- ~~Auto GROUP BY UI~~ → future; keep derivations/mappings model extensible  

**Deferred UI (future-ready)**

- GROUP BY configuration block when compiler supports it  
- Additional `on_conflict` strategies beyond current five  

---

## 6. Step-by-step workflows

### 6.1 Connections (M1) and file sources (M1b)

1. Render `connections` registry; empty state → **Add connection** or **Add file source**.
2. Modal: pick **connector** (database or file) → `auth_method` if applicable → connector-specific fields (§7.2.9).
3. **Test / verify** (required) → success/failure UI.
   - Database: live connectivity test (existing).
   - File: path/S3/upload reachable; header row parsed from **sample read** (first ~64KB–1MB).
4. **Save** → store under connection key (`connection_ref` name).
5. Auto-open from wizard if blueprint references missing connection.

### 6.2 Blueprint B1 — Sources & joins

1. **Left pane:** `SchemaTree` + connection switcher.
2. Introspection API loads:
   - **Database connections:** schemas → tables → columns.
   - **S3 file connections:** file list under prefix (`CSV_S3_BUCKET`).
   - **Local / staged file connections:** registered files + columns from sample header (`LOCAL_CSV`).
3. **Right pane:** Source graph canvas.
4. **Set as root table** → `sources.root_table` (alias, schema, table, or `file_name` for file sources).
5. **Add join** → `joins[]`: connection, join_type (`INNER`, `LEFT`, `RIGHT`, `FULL`), alias, schema/table or file.
6. **Join conditions:** free-text `left_expression`, `operator`, `right_expression` (supports `CASE WHEN` etc.).

### 6.3 Blueprint B2 — Target & conflict

1. Target connection dropdown (from M1).
2. Introspection: schema → table list → select `target.schema`, `target.table_name`.
3. **Reflection:** load target columns (required for B3 grid).
4. Primary keys: multi-select checkboxes → `primary_keys[]`.
5. **on_conflict** (all five):
   - `FAIL`
   - `IGNORE`
   - `UPSERT`
   - `IGNORE_AND_LOG`
   - `IGNORE_AND_INSERT_UNPROCESSED`
6. When `IGNORE_AND_INSERT_UNPROCESSED`:
   - Field: `unprocessed_table` (schema.table)
   - Action: **Create on target** — API copies target table DDL structure (no data) and creates unprocessed table (implementation detail TBD).
7. When `IGNORE_AND_LOG`:
   - UI proposes an **audit / conflict log table** derived from blueprint context (see [§12.4](#124-ignore_and_log-audit-table-oq-8)).
   - User can accept default or edit name; optional **Create on target** with suggested column structure.

**Note:** v1 compile dialect is MySQL; target connection may still be typed as MYSQL/MSSQL/POSTGRESQL in config for documentation — generator connectivity rules apply on validate.

### 6.4 Blueprint B3 — Mappings & derivations

1. **Derivations drawer:** `variable_name` + `SqlCodeEditor` for `expression`.
2. **Mapping grid:** one row per target column from B2 introspection.
3. Per row:
   - `source_type`: DIRECT | CONSTANT | DERIVED | EXPRESSION
   - `source_value` (control varies by type)
   - `cast_to` (default from target column type)
   - `is_nullable` (checkbox)
   - ~~`fallback_value`~~ omitted in v1
4. DIRECT: dropdown of source aliases/columns from B1.

### 6.5 Blueprint B4 — Filters & chunking

1. **Pre-filters:** list editor → `pre_filters[]` (SQL predicates).
2. **Post-filters:** list editor → `post_filters[]`.
3. **Chunking:** toggle `chunking_strategy.is_enabled`.
   - If enabled: `chunk_by_column`, `chunk_size` (required).
   - If disabled: `chunk_by_column` and `chunk_size` null.

### 6.6 Migration review & export

1. Summary: all blueprints, connection refs, validation status.
2. **Validate** (full migration) via config API → script-generator `POST /validate`.
3. Show errors with `code`, `path`, `blueprint_sequence` (match engine report).
4. **Download JSON** — **disabled until validation passes** (OQ-1).

**v1 does not require** Generate SQL button; add in v1.1 via same API proxy.

### 6.7 Draft storage (OQ-3)

User chooses how drafts are persisted (both supported in v1):

| Mode | Behaviour |
|------|-----------|
| **Server** | Migration saved via config API (SQLite/Postgres TBD); multi-device, survives browser clear |
| **Local** | Migration saved in browser `localStorage` / IndexedDB; works offline; export still produces same JSON |

**UX:** On first save or in migration settings: *“Save to server”* / *“Save locally only”* (or both — server as source of truth with local cache). Export JSON is identical regardless of storage mode.

---

## 7. Connection storage (recommendation)

You asked for pros/cons of structured fields vs raw URI.

### Option A — Structured fields (recommended; evolving to connectors)

UI stores **connector-specific payloads** validated by each adapter (§7.2). Legacy flat `host` / `port` / `username` / `password` is replaced by `connector_id` + structured `connector_payload`.

Config API **assembles** export fields (`connection_string`, S3 URI, file refs, `auth_method`, `driver_options`) per connector.

| Pros | Cons |
|------|------|
| Better UX and validation | Assembly logic per connection type in API |
| Easier **Test connection** | Must stay in sync with parser expectations |
| Mask password fields in UI | — |
| Matches how users think | — |

### Option B — Raw URI only

| Pros | Cons |
|------|------|
| Power users, copy-paste | Easy to mistype |
| No assembly layer | Poor test-connection UX |
| — | Harder to rotate single fields |

### Recommendation

**v1: Option A (structured)** with optional **“Advanced: edit connection string”** toggle for power users. Export always produces valid `connection_string` / S3 fields per [sampleConfigfile.json](../docs/sampleConfigfile.json).

**Secrets:** Store and export credentials in JSON for now; document that production will use Key Vault references (schema extension TBD).

---

## 7.1 File sources (CSV extracts)

Architects often receive **CSV extracts** (sometimes very large) as migration sources. The platform must make this easy without moving multi-GB files through the browser or embedding file bytes in exported JSON.

### 7.1.1 Core principle: design-time vs run-time

| Phase | Product | What happens to the CSV |
|-------|---------|-------------------------|
| **Design** | Config platform (UI + API) | Register **file reference** + **parse options** + **column preview** from a tiny sample |
| **Export** | Config API | JSON contains `connection_ref`, `location_kind`, path/URI, `file_name`, parse options — **never file bytes** |
| **Run** | **Migrator** (and operator pre-steps) | Resolve file location, **stream** stage near target DB, `LOAD DATA` / temp bootstrap, execute generated SQL |

Config platform **authors** where the file lives and how to parse headers. **Migrator** owns moving and loading the full file at execution time (see [../script-generator/docs/executor-streaming-design.md](../script-generator/docs/executor-streaming-design.md): stream file chunks; never read full file to RAM).

```text
Architect (browser)  →  Config API  →  sample read only (headers)
                              ↓
                        export config.json (metadata only)
                              ↓
                        Migrator  →  resolve path/S3/staging  →  stream load  →  target DB
```

### 7.1.2 Connection type: `LOCAL_CSV`

Add a new connection type alongside `CSV_S3_BUCKET`:

| Field | Purpose |
|-------|---------|
| `type` | `LOCAL_CSV` |
| `location_kind` | `local_path` \| `platform_staging` (use `csv_s3_bucket` connector for S3 — not `LOCAL_CSV`) |
| `file_path` | Absolute or workspace-relative path when `location_kind = local_path` |
| `staging_file_id` | Internal id when uploaded to platform staging |
| `parse_options` | `delimiter`, `quote`, `header_row`, `encoding` |

S3 bucket fields (`s3_bucket_uri`, `aws_region`) belong to **`csv_s3_bucket`** / export `type` `CSV_S3_BUCKET` only — not `LOCAL_CSV`.

**Recommendation:** Keep **`CSV_S3_BUCKET`** for remote bucket prefixes; add **`LOCAL_CSV`** for path-based and platform-staged files. Blueprint `sources.*.file_name` stays unchanged.

Example export fragment:

```json
"connections": {
  "client_extract_csv": {
    "type": "LOCAL_CSV",
    "location_kind": "local_path",
    "file_path": "/data/extracts/customers.csv",
    "parse_options": {
      "delimiter": ",",
      "quote": "\"",
      "header_row": 1,
      "encoding": "utf-8"
    }
  }
}
```

Script-generator adds a **`LocalCsvSourceBootstrapStrategy`** (parallel to `S3CsvSourceBootstrapStrategy`) emitting path variables and `LOAD DATA LOCAL INFILE` / federated staging preamble. Contract extension coordinated via [sampleConfigfile.json](../docs/sampleConfigfile.json).

### 7.1.3 Three ingestion modes (support all; UI guides by size)

| Mode | Connector / `location_kind` | Best for | UX |
|------|---------------------------|----------|-----|
| **A — Local / server path** | `local_csv` · `local_path` | **Huge files** when API/migrator share disk or mounted volume | User enters path (e.g. `D:\migrations\extracts\customers.csv`). **Test** checks exists, readable, CSV header sample. |
| **B — Object storage (S3)** | `csv_s3_bucket` · `CSV_S3_BUCKET` | **Huge files** in enterprise (multi-GB) | Bucket URI + list `*.csv` + pick `file_name`. **Recommended happy path** for large extracts. |
| **C — Platform upload** | `local_csv` · `platform_staging` | Small/medium files; hosted web UI without S3 | Drag-and-drop → API stores under `data/staging/{migration_id}/{file_id}.csv`. **Size-capped**; resumable upload for larger uploads (OQ-12). |

#### Size policy (UI defaults)

| File size | Default guidance |
|-----------|------------------|
| &lt; ~50 MB | Upload, path, or S3 |
| ~50 MB – few GB | **Path or S3** — discourage simple upload |
| Multi-GB | **S3 or shared mount only** — disable naive browser upload; show setup instructions |

### 7.1.4 Introspection for file sources

Unlike SQL sources, file sources have no `information_schema`. Introspection means:

1. **List files** — S3 prefix listing (`CSV_S3_BUCKET`) or registered path/upload entries (`LOCAL_CSV`).
2. **Column preview (required for `LOCAL_CSV`; optional for S3 in v1 — OQ-7)** — read **first ~64KB–1MB only** (local seek, S3 `Range` GET, or staged file head). Parse header row (+ optional first N data rows for type hints). **Never** load full file in config API.
3. User picks `file_name` for root or join; columns populate `SchemaTree` for B3 mapping.

### 7.1.5 Config API responsibilities (file sources)

| Area | Endpoints (illustrative) | Notes |
|------|--------------------------|-------|
| File source CRUD | Extend `POST/PUT/GET/DELETE /connections` | `LOCAL_CSV` payload shape |
| Verify file | `POST /connections/test` | Path exists / S3 reachable / upload complete + header parse |
| List files | `GET /connections/{ref}/files` | S3 list or single registered local file |
| Column preview | `GET /connections/{ref}/files/{name}/columns` | Sample read only |
| Upload | `POST /connections/{ref}/files/upload` | Optional; chunked/resumable when implemented |
| Staging cleanup | On migration delete / TTL job | Remove uploaded blobs (OQ-12) |

### 7.1.6 Security and deployment

| Concern | Mitigation |
|---------|------------|
| **Arbitrary path read** (hosted API) | **Allowlist** staging roots (e.g. `CONFIG_API_FILE_ROOTS`); reject `..` traversal |
| **Local path on architect laptop** | Supported when API runs locally (§1.4 local stack); path must exist on **migrator host** at run time, not only UI machine |
| **PII in uploads** | Retention policy + encryption at rest (production); document in ops runbook |
| **Upload DoS** | Hard max size, rate limits, per-migration quota |

### 7.1.7 Cross-product scope

| Product | File-source work |
|---------|------------------|
| **config-platform** | M1b UI, file registry, sample introspection, export `LOCAL_CSV` |
| **script-generator** | `LocalCsvSourceBootstrapStrategy`; validate file refs in config |
| **migrator** | **Resolve** `file_path` / S3 URI / `staging_file_id` at run time; **stream** stage; pre-flight “file exists” before execute |

### 7.1.8 Out of scope (v1 file sources)

| Item | Notes |
|------|-------|
| **`LOCAL_XLSX`** | Deferred — sheet picker, conversion to CSV at run time (OQ-14) |
| **Full file upload for multi-GB** | Not required; use path or S3 |
| **Embedding file bytes in JSON** | Never |

---

## 7.2 Connection connectors & authentication

Flat `DatabaseConnectionFields` (one form for MySQL, MSSQL, PostgreSQL) **does not work** for real deployments: on-prem SQL Server (Windows vs SQL auth), Azure SQL Database (many Entra modes), SSL/TLS variants, and S3 credential models all need different fields and test logic.

### 7.2.1 Architecture: registry + adapter

Each saved connection stores:

| Field | Purpose |
|-------|---------|
| `ref` | Stable key used in blueprints (`connection_ref`) |
| `connector_id` | Selects adapter implementation and UI form |
| `connector_payload` | JSON document validated by that adapter |
| `secret_ref` | Optional Key Vault pointer (OQ-9) |

**Factory (API):** `ConnectorRegistry.get(connector_id)` → `IConnectionConnector` implementing:

| Method | Purpose |
|--------|---------|
| `metadata()` | Label, description, supported `auth_method` values for UI |
| `validate(payload)` | Pydantic / business rules |
| `fingerprint(payload)` | Hash for test-before-save token (excludes rotating secrets) |
| `test_connect(payload)` | Live probe from API host |
| `build_export(payload)` | Contract JSON fragment for migration export |
| `create_engine(payload)` | SQLAlchemy / driver handle for introspection (DB connectors only) |

**UI:** one React form component per Phase 1 `connector_id` (or shared sub-forms per `auth_method`). Web **never** opens DB connections directly.

**Export `type` (coarse, script-generator):** `MYSQL` \| `MSSQL` \| `POSTGRESQL` \| `CSV_S3_BUCKET` \| `LOCAL_CSV` — derived from `connector_id`. Rich auth detail lives in extended export fields (OQ-18).

```text
User picks connector  →  auth_method (if applicable)  →  dynamic fields
        →  Test  →  Save (connector_id + payload)
        →  Export (type + connection_string + auth_method + driver_options + secret_ref)
```

### 7.2.2 Phase 1 connector catalog

| # | `connector_id` | Export `type` | Category |
|---|----------------|---------------|----------|
| 1 | `local_csv` | `LOCAL_CSV` | File |
| 2 | `mssql_onprem` | `MSSQL` | Database |
| 3 | `azure_sql_database` | `MSSQL` | Database (Azure SQL / **ADB**) |
| 4 | `mysql` | `MYSQL` | Database |
| 5 | `postgresql` | `POSTGRESQL` | Database |
| 6 | `csv_s3_bucket` | `CSV_S3_BUCKET` | File |

**Phase 1 goal:** every row above has adapter + UI form + test + export + introspection (where applicable). P1 (already delivered) used a simplified generic form; **P1.1** refactors to this catalog.

Auth methods are **not** all built in one release. Delivery tiers (§7.2.2a) prioritize repeatable, testable connections; exotic or token-paste flows are deferred.

### 7.2.2a Phased auth delivery (must / should / defer)

**Rule:** Config platform stores **connection intent** (`auth_method`, IDs, `driver_options`, `secret_ref`). **Migrator** acquires short-lived tokens (Entra, RDS IAM, STS) at run time (OQ-21). Phase 1 UI only includes auth modes where test-from-API is meaningful and export does not rely on pasted disposable tokens.

#### Must-have — **P1.1–P1.2** (ship first)

| Connector | `auth_method` / access |
|-----------|------------------------|
| `mssql_onprem` | `sql_login`, `windows_integrated`, `windows_login` |
| `azure_sql_database` | `sql_login`, `entra_service_principal` |
| `mysql` | `password` (optional single SSL toggle) |
| `postgresql` | `password` + `sslmode` dropdown |
| `csv_s3_bucket` | `access_key` |

`local_csv` is **not** in P1.2 — delivered in **P1.5** (connector) + **P3.5** (wizard / SchemaTree wiring). See §11.1.

#### Should-have — **P1.3–P1.4** (next)

| Connector | Add |
|-----------|-----|
| `azure_sql_database` | `entra_managed_identity`, `entra_password` |
| `mysql` | full `ssl_mode` matrix; `entra_service_principal`, `entra_managed_identity` (Azure MySQL) |
| `postgresql` | `password_ssl_client_cert`; `entra_password`, `entra_service_principal`, `entra_managed_identity` (Azure PG) |
| `csv_s3_bucket` | `session_token`, `instance_profile`, `assume_role` |
| `mssql_onprem` | `ntlm` (only if `windows_login` insufficient in target environments) |

#### Deferred — **post P1.4** (documented; not Phase 1 UI)

| Item | Target phase | Reason |
|------|--------------|--------|
| `access_token` (Azure SQL) | API/CI only; no Connect UI | Short TTL; paste-token security risk |
| `entra_interactive` (MFA) | With platform login (OQ-10) | Browser OAuth |
| `gssapi` (PostgreSQL Kerberos) | P1.7+ | Requires Kerberos ticket on API host |
| `mysql_rds_iam` / `postgresql_rds_iam` | **P1.6+** | AWS-specific; migrator token acquisition |
| `unc_username` / `unc_password` (`local_csv`) | P1.7+ | Prefer pre-mounted paths on migrator host |
| Client certificate auth (MySQL) | P1.7+ | Enterprise edge case |

---

### 7.2.3 `mssql_onprem` — on-premises Microsoft SQL Server

**When:** Default instance or named instance on corporate network (`host\INSTANCE`, port 1433 or custom).

#### Authentication methods

| `auth_method` | UI label | Delivery | Required fields | How API tests |
|---------------|----------|----------|-----------------|---------------|
| `sql_login` | SQL Server authentication | **P1.2** | `host`, `port`, `database`, `username`, `password` | ODBC `UID`/`PWD`; `SELECT 1` |
| `windows_integrated` | Windows integrated security | **P1.2** | `host`, `port`, `database` | `Trusted_Connection=yes` — **Windows identity of config API process** |
| `windows_login` | Windows authentication (explicit) | **P1.2** | `host`, `port`, `database`, `domain`, `username`, `password` | `DOMAIN\user` + password via ODBC |
| `ntlm` | NTLM (domain user) | **P1.4** | Same as `windows_login` | NTLM ODBC path when integrated auth unavailable |

#### Deferred

| `auth_method` | Notes |
|---------------|-------|
| — | (none beyond `ntlm` timing) |

#### Common options (all auth methods)

| Field | Default | Notes |
|-------|---------|-------|
| `encrypt` | `true` (2019+) | Maps to ODBC `Encrypt` |
| `trust_server_certificate` | `false` on-prem | `true` only when org policy allows (dev/lab) |
| `instance_name` | optional | Named instance; combined with `host` |
| `connection_timeout_seconds` | `30` | Test + introspection |
| `application_intent` | `ReadOnly` optional | For read replicas / AG secondary |

#### Constraints

| Topic | Rule |
|-------|------|
| **Windows integrated** | Only supported when config API runs on **Windows** joined to the domain (or gMSA). Linux-hosted API: show clear error — use `sql_login` or `windows_login`. |
| **Export** | `auth_method` + `driver_options` always emitted; password via `secret_ref` when vault enabled |
| **Advanced** | Optional raw ODBC connection string override (power users); invalidates standard fingerprint unless canonicalized |

---

### 7.2.4 `azure_sql_database` — Azure SQL Database (ADB)

**When:** Server host `*.database.windows.net` (single database or logical server). **Azure SQL Managed Instance** uses the same connector with MI endpoint host and firewall rules — no separate `connector_id` in v1.

**Not the same connector as `mssql_onprem`** — different defaults (`encrypt=true`, `trust_server_certificate=false`, firewall, Entra).

#### Authentication methods

| `auth_method` | UI label | Delivery | Required fields | How API tests |
|---------------|----------|----------|-----------------|---------------|
| `sql_login` | SQL authentication | **P1.2** | `server`, `database`, `username`, `password` | Port 1433; helper text for `user@servername` format |
| `entra_service_principal` | Microsoft Entra ID (service principal) | **P1.2** | `server`, `database`, `tenant_id`, `client_id`, `client_secret` or `client_certificate` | Client credentials → token → ODBC |
| `entra_password` | Microsoft Entra ID (user/password) | **P1.3** | `server`, `database`, `entra_user`, `entra_password`, `tenant_id` | Token via identity library → connect |
| `entra_managed_identity` | Managed identity | **P1.3** | `server`, `database`, optional `managed_identity_client_id` | `DefaultAzureCredential` on API host in Azure |

#### Deferred (not Connect UI in Phase 1)

| `auth_method` | Target | Reason |
|---------------|--------|--------|
| `access_token` | API/CI automation only | Short TTL; discourages paste-token in UI (OQ-22) |
| `entra_interactive` (MFA, Universal) | With platform login (OQ-10) | Browser OAuth from config API |
| `entra_default_credential` (developer CLI) | Dev-only | Not for production config API |

#### Common options (all auth methods)

| Field | Default | Notes |
|-------|---------|-------|
| `encrypt` | `true` | Required for Azure SQL |
| `trust_server_certificate` | `false` | |
| `host_name_in_certificate` | `*.database.windows.net` | Optional override |
| `connection_timeout_seconds` | `30` | |

#### Run-time note (migrator)

Entra-based connections: exported config stores **`auth_method` + non-secret IDs**; **migrator** (or API at test-only) acquires fresh tokens at execution. Long-lived tokens are **not** stored in exported JSON (OQ-21).

---

### 7.2.5 `mysql` — MySQL (on-prem, VM, RDS, Azure Database for MySQL)

**When:** MySQL 5.7+, 8.x, MariaDB-compatible where driver supports.

#### Authentication methods

| `auth_method` | UI label | Delivery | Required fields | How API tests |
|---------------|----------|----------|-----------------|---------------|
| `password` | Username & password | **P1.2** | `host`, `port`, `database`, `username`, `password`; optional SSL toggle | `mysql+pymysql`; `SELECT 1` |
| `password_ssl` | Username & password (full SSL) | **P1.4** | Above + `ssl_mode`, optional `ssl_ca_path` | TLS per mode |
| `entra_service_principal` | Azure Entra (service principal) | **P1.3** | Azure MySQL host, `database`, `tenant_id`, `client_id`, `client_secret`, `entra_user` | Azure token plugin |
| `entra_managed_identity` | Azure Entra (managed identity) | **P1.3** | `host`, `database`, `entra_user`, optional MI client id | API on Azure only |

#### SSL / TLS (`ssl_mode` when `password_ssl` or optional on `password`)

| Value | Meaning |
|-------|---------|
| `DISABLED` | No TLS (lab only; warn in UI) |
| `PREFERRED` | TLS if server supports |
| `REQUIRED` | TLS required; no cert verify |
| `VERIFY_CA` | TLS + verify CA |
| `VERIFY_IDENTITY` | TLS + verify hostname |

#### Common options

| Field | Notes |
|-------|-------|
| `default_auth_plugin` | Hint for `caching_sha2_password` vs `mysql_native_password` (driver auto when possible) |
| `charset` | Default `utf8mb4` |

#### Deferred

| Item | Target | Notes |
|------|--------|-------|
| `rds_iam` (`mysql_rds_iam`) | **P1.6+** | AWS RDS IAM DB auth; migrator acquires token at run |
| Client certificate auth | P1.7+ | Enterprise edge case |

---

### 7.2.6 `postgresql` — PostgreSQL (on-prem, RDS, Azure Database for PostgreSQL)

#### Authentication methods

| `auth_method` | UI label | Delivery | Required fields | How API tests |
|---------------|----------|----------|-----------------|---------------|
| `password` | Password | **P1.2** | `host`, `port`, `database`, `username`, `password`, `sslmode` | `postgresql+psycopg2`; `SELECT 1` |
| `password_ssl_client_cert` | Password + client certificate | **P1.4** | Above + `sslrootcert`, `sslcert`, `sslkey` | mTLS |
| `entra_password` | Microsoft Entra (user) | **P1.3** | Azure PG host, `database`, `entra_user`, `entra_password`, `tenant_id` | Azure AD token as password |
| `entra_service_principal` | Microsoft Entra (service principal) | **P1.3** | `tenant_id`, `client_id`, `client_secret`, `entra_user` | Token → connect |
| `entra_managed_identity` | Managed identity | **P1.3** | Azure PG host, `database`, `entra_user`, optional MI client id | API on Azure |

#### `sslmode` (libpq semantics — show dropdown for all password-based methods)

| Value | Use |
|-------|-----|
| `disable` | Lab only (warn) |
| `allow` | Try non-SSL first |
| `prefer` | Default many installs |
| `require` | TLS required |
| `verify-ca` | Verify server CA |
| `verify-full` | Verify CA + hostname |

#### Deferred

| Item | Target | Notes |
|------|--------|-------|
| `gssapi` (Kerberos) | P1.7+ | API host must hold valid Kerberos ticket |
| `peer` / `trust` | — | Local socket only; not for remote config API |
| `rds_iam` (`postgresql_rds_iam`) | **P1.6+** | AWS RDS IAM DB auth; migrator token at run |

---

### 7.2.7 `local_csv` — local / staged CSV

See §7.1. Phase 1 treats this as a **connector** (not a database).

#### “Authentication” = access mode (no DB login)

| `location_kind` | UI | Delivery | Verify (test) |
|-----------------|-----|----------|---------------|
| `local_path` | Absolute or allowlisted path; UNC path as text only (no creds in v1) | **P1.5** | File exists, readable, CSV header sample |
| `platform_staging` | Upload widget (size-capped) | **P1.5** (with P3.5) | Staged blob + header sample |

#### Payload fields

| Field | Notes |
|-------|-------|
| `file_path` / `staging_file_id` | Per §7.1 |
| `parse_options` | `delimiter`, `quote`, `header_row`, `encoding` |

#### Deferred

| Field | Target | Notes |
|-------|--------|-------|
| `unc_username`, `unc_password` | P1.7+ | Prefer pre-mounted share on migrator/API host |

**Export `type`:** `LOCAL_CSV`. No `connection_string`.

---

### 7.2.8 `csv_s3_bucket` — CSV on Amazon S3

#### Authentication methods

| `auth_method` | UI label | Delivery | Required fields | How API tests |
|---------------|----------|----------|-----------------|---------------|
| `access_key` | AWS access key | **P1.2** | `s3_bucket_uri`, `aws_region`, `access_key_id`, `secret_access_key` | `head_bucket` + list prefix |
| `session_token` | Temporary credentials | **P1.4** | Above + `session_token` | STS/session creds |
| `instance_profile` | IAM role (API host) | **P1.4** | `s3_bucket_uri`, `aws_region` | boto3 default chain; API on AWS |
| `assume_role` | Assume IAM role | **P1.4** | `role_arn`, optional `external_id`, `s3_bucket_uri`, `aws_region` | STS `AssumeRole` |

#### Deferred / unsupported

| Item | Notes |
|------|-------|
| Anonymous public bucket | Read-only; warn; not default |
| Azure Blob / GCS | Separate future connectors (`azure_blob_csv`, `gcs_csv`) |

#### Introspection

List `*.csv` under prefix; optional column sample (OQ-7).

---

### 7.2.9 UI flow (Connect dialog)

```text
1. Category:     [ Database ] [ File ]
2. Connector:    e.g. "Azure SQL Database" | "SQL Server (on-prem)" | …
3. Auth method:  radio / dropdown (options from connector metadata())
4. Fields:       connector-specific form only
5. Test          required
6. Save
```

Changing connector or `auth_method` clears verification token and sensitive fields.

### 7.2.10 Export shape (extended contract)

Example (Azure SQL, service principal):

```json
{
  "type": "MSSQL",
  "auth_method": "entra_service_principal",
  "connection_string": "sqlserver://myserver.database.windows.net:1433/mydb",
  "driver_options": {
    "encrypt": true,
    "trust_server_certificate": false
  },
  "entra": {
    "tenant_id": "…",
    "client_id": "…"
  },
  "secret_ref": "keyvault://vault/sp-secret"
}
```

Secrets (`password`, `client_secret`, `access_key`) go to **`secret_ref`** in production; interim export may inline (stakeholder decision §1.3).

Script-generator and migrator consume `type` + `auth_method` + `driver_options`; token acquisition at run for Entra/MI/IAM (OQ-21).

#### Cross-product consumers (script-generator / migrator)

P1.2 export extends the shared contract in [sampleConfigfile.json](../docs/sampleConfigfile.json). **Config platform** authors the new fields; **downstream products must stay in sync** or `validate` / `generate` will fail on exported JSON.

| Consumer | Minimum (required when P1.2 export ships) | Full auth (later) |
|----------|-------------------------------------------|-------------------|
| **script-generator** | Extend `DatabaseConnection` / `CsvS3Connection` models to **parse and validate** optional `auth_method`, `driver_options`, `access_key_id`, `entra`, `secret_ref` (today: `extra="forbid"` rejects them). **Compilation may still use** `connection_string` / `s3_bucket_uri` + `aws_region` until bootstrap is auth-aware. | Use `auth_method` + `driver_options` in `SourceBootstrapCompiler` when credentials are not fully embedded in `connection_string` (Entra SP, Windows auth, S3 keys, SSL flags). |
| **migrator** | Accept same connection shape in execution config | Acquire tokens / resolve `secret_ref` at run time per `auth_method` (OQ-21) |

**Rule:** Updating `sampleConfigfile.json` for P1.2 **without** updating script-generator connection models breaks the golden sample and any config exported from Connect. Track in [script-generator/docs/REQUIREMENTS.md](../script-generator/docs/REQUIREMENTS.md) §9 (contract-sync phase).

### 7.2.11 API endpoints (connectors)

| Endpoint | Purpose |
|----------|---------|
| `GET /connectors` | List Phase 1 `connector_id`, labels, categories |
| `GET /connectors/{id}/schema` | Optional JSON schema per `auth_method` (or UI-hardcoded v1) |
| `POST /connections/test` | Body includes `connector_id` + `connector_payload` |
| CRUD `/connections` | Persist `connector_id` + payload (replaces flat `type` + `database`) |

Backward compatibility: migrate stored P1 connections to `mssql_onprem` + `sql_login` payload on read.

### 7.2.12 Implementation phases (connectors)

Aligned with §7.2.2a delivery tiers:

| Phase | Scope | Exit criteria |
|-------|--------|---------------|
| **P1.1** | Connector registry + adapter interface | Factory, `IConnectionConnector`, migrate P1 flat fields to `connector_id` + payload |
| **P1.2** | **Must-have auth** (§7.2.2a) | `mssql_onprem` SQL + Windows; `azure_sql_database` SQL + Entra SP; `mysql`/`postgresql` password; S3 `access_key`; basic test + export |
| **P1.3** | **Should-have — Entra** | Azure SQL / PG / MySQL: `entra_managed_identity`, `entra_password`, Entra SP on PG/MySQL |
| **P1.4** | **Should-have — SSL & AWS roles** | Full MySQL SSL; PG client cert; S3 `session_token`, `instance_profile`, `assume_role`; `mssql_onprem` `ntlm` if needed |
| **P1.5** | `local_csv` connector | `local_path` + `platform_staging` (align P3.5) |
| **P1.6** | AWS RDS IAM | `mysql_rds_iam`, `postgresql_rds_iam` auth methods; migrator token story |
| **P1.7+** | Edge auth | `gssapi`, UNC creds, MySQL client cert, `access_token` API hook |

P1.1–P1.4 can proceed in parallel with P2/P3 where they only touch the Connect module.

### 7.2.13 Out of scope / deferred (connectors)

| Item | Notes |
|------|-------|
| Oracle, DB2, Snowflake | Future connectors |
| Interactive Entra MFA in browser | Platform auth (OQ-10) first |
| `access_token` in Connect UI | API/CI only (OQ-22); short-lived paste-token |
| Storing long-lived access tokens in export | Forbidden |
| Config UI user login / RBAC | OQ-10 |
| AWS RDS IAM | **P1.6+** — not P1.2–P1.4 |
| PostgreSQL `gssapi` / UNC file creds | **P1.7+** |

---

## 8. Validation strategy (recommendation)

You asked when to validate — direct mappings need little; expressions need engine whitelist checks.

### Three layers

| Layer | When | What |
|-------|------|------|
| **L1 — Form** | On blur / Next | Required fields, types, connection tested, refs exist |
| **L2 — Expression** | On blur in `SqlCodeEditor` or leaving B1/B3/B4 | Async call to generator validate (subset or full config) |
| **L3 — Full** | Migration Review before download | Complete `POST /validate` |

### Recommendation

- **Do not** run full engine validation on every **Next** (too slow, noisy).
- **Do** run L1 on every Next (block if fail).
- **Do** run L2 debounced (500ms) on expression fields; show inline warnings/errors.
- **Do** run L3 on Review; **block Download** if invalid.

**Confirmed** per OQ-2 (§12.0). Layer details above are normative.

---

## 9. Config API (FastAPI) — responsibilities

| Area | Endpoints (illustrative) | Notes |
|------|--------------------------|-------|
| Migrations CRUD | `GET/POST/PUT/DELETE /migrations` | Draft storage (JSON file today) |
| Migration blueprints | `POST/DELETE .../blueprints`, `.../duplicate`, `PUT .../reorder` | Blueprint sub-resources (P2) |
| Connections CRUD | `GET/POST/PUT/DELETE /connections` | `connector_id` + payload (P1.1+) |
| Connections export | `GET /connections/export` | Contract-shaped connection map |
| Connections test | `POST /connections/test` | Required before save (§7.2) |
| Connectors catalog | `GET /connectors`, `GET /connectors/{id}/schema` | UI metadata (§7.2.11) |
| Metadata (SQL) | `GET /connections/{ref}/schemas`, `.../tables`, `.../columns` | DB introspection |
| Metadata (files) | `GET /connections/{ref}/files`, `.../files/{name}/columns` | S3 list + sample column preview (§7.1) |
| File upload | `POST /connections/{ref}/files/upload` | Size-capped staging (OQ-12; P3.5) |
| Target DDL | `POST /connections/{ref}/tables/copy-structure` | For `unprocessed_table` (P6) |
| Export | `GET /migrations/{id}/export` | Produces contract JSON |
| Validate proxy | `POST /migrations/{id}/validate` | Forwards to script-generator (P5) |

Frontend **never** calls script-generator directly (per [INTEGRATION.md](../docs/INTEGRATION.md)).

### FastAPI concerns (brief)

| Concern | Mitigation |
|---------|------------|
| Credential handling | Never log passwords/tokens/keys; HTTPS only; `secret_ref` for production (§7.2.10) |
| Connector-specific auth | Each adapter sanitizes driver errors; Windows/Entra failures get actionable messages (§7.2) |
| SQL injection in introspection | Parameterized metadata queries only |
| Path traversal (file sources) | Allowlisted roots; no arbitrary server paths in hosted mode (§7.1.6) |
| Large file handling | Sample-only reads in API; full streaming in migrator (§7.1.1) |
| CORS | Restrict to web origin in dev/prod |
| Rate limiting | On test-connection and validate |

No blocker for v1; standard practices apply.

---

## 10. Frontend structure

```text
config-platform/
├── api/                    # FastAPI service
└── web/                    # React + TypeScript
    └── src/
        ├── components/
        │   ├── connections/
        │   │   ├── ConnectionFormDialog.tsx      # connector picker shell (P1.1+ target)
        │   │   ├── connectors/                   # planned (P1.1+)
        │   │   │   ├── MssqlOnPremForm.tsx
        │   │   │   ├── AzureSqlDatabaseForm.tsx
        │   │   │   ├── MySqlForm.tsx
        │   │   │   ├── PostgreSqlForm.tsx
        │   │   │   ├── LocalCsvForm.tsx
        │   │   │   └── S3BucketForm.tsx
        │   │   └── connectorRegistry.ts
        │   ├── shared/
        │   │   ├── SchemaTree.tsx               # DB + S3 + local file columns
        │   │   └── SqlCodeEditor.tsx
        │   └── config_wizard/
        │       ├── MigrationHeaderForm.tsx    # M0
        │       ├── BlueprintList.tsx            # M2
        │       ├── WizardContainer.tsx          # planned (P3)
        │       ├── StepSourcesJoins.tsx         # planned (P3)
        │       ├── StepTargetConflict.tsx       # planned (P3)
        │       ├── StepMappings.tsx             # planned (P3)
        │       └── StepFiltersChunking.tsx      # planned (P3)
        └── views/
            ├── ConnectionsView.tsx
            ├── ConfigBuilderView.tsx
            ├── MigrationRunnerView.tsx          # placeholder
            ├── DatabaseStudioView.tsx           # placeholder
            └── ValidationEngineView.tsx         # placeholder
```

### UI / security principles

- Open-source component library: **MUI (Material UI) + MUI X Data Grid** (OQ-4)
- **API-first client:** one `api/` module; env-based base URL (§1.4)
- No secrets in browser storage (session/server-side preferred for drafts)
- Sanitize displayed error messages from DB drivers
- CSP, dependency scanning in CI
- Role-based access — **deferred** (OQ-10; far future)

---

## 11. Implementation phases (step-by-step plan)

**Status legend:** `[x]` = complete · `[ ]` = not started / in progress

Update tick marks in this section as you finish each item. §11.1 is the quick phase summary.

### Phase P0 — Shell, routes, sidebar wizard

- [x] App shell — persistent left nav, workspace layout (`AppLayout.tsx`)
- [x] Nav slots — Connect + Configs active; Run / Studio / Validate placeholders (`navigation.ts`, placeholder views)
- [x] Routes — `/connections`, `/migrations`, `/migrations/:id`, `/run`, `/studio`, `/validation`
- [x] Blueprint wizard **sidebar layout** (Layout B, OQ-5) — `BlueprintWizardLayoutSidebar.tsx`
- [x] Wizard step definitions B1–B5 (`types.ts`); mock step content (`WizardStepMock.tsx`)
- [x] API-first client — `VITE_API_URL`, single `api/` module
- [x] MUI + TypeScript stack; FastAPI bootstrap (CORS, logging, health)
- [ ] MUI X Data Grid used in a real screen (dependency installed; mapping grid is P3)
- [ ] Draft storage UX — server vs local user choice (OQ-3; API stores server-side today)

**Exit criteria:** Nav works; sidebar chosen for blueprint steps; all future nav routes registered.

### Phase P1 — Connections (flat fields; superseded by P1.1+)

- [x] API CRUD — `GET/POST/PUT/DELETE /connections`
- [x] Test endpoint + verification token — `POST /connections/test`; test required before save
- [x] Flat models — `MYSQL`, `MSSQL`, `POSTGRESQL`, `CSV_S3_BUCKET`
- [x] Connection string export — `GET /connections/export`
- [x] UI — connection list, dialog, DB form, S3 form (`ConnectionsView`, `ConnectionFormDialog`)
- [x] API tests — connections, builder, service, store
- [x] Optional `secret_ref` on API model (no UI field yet)
- [ ] S3 access-key fields in form (boto3 default chain only today)
- [ ] SSL / driver options in forms

**Exit criteria:** All four legacy connection types testable and exportable. **Refactor to connectors in P1.1.**

### Phase P1.1 — Connector registry + adapter interface

- [x] `connector_id` + `connector_payload` on saved connections (replace flat `type` + blocks)
- [x] `IConnectionConnector` + `ConnectorRegistry` factory (API)
- [x] Adapter methods — `metadata`, `validate`, `fingerprint`, `test_connect`, `build_export`, `create_engine`
- [x] `GET /connectors`, `GET /connectors/{id}/schema`
- [x] Six Phase 1 connectors registered — `local_csv`, `mssql_onprem`, `azure_sql_database`, `mysql`, `postgresql`, `csv_s3_bucket`
- [x] Connect UI — connector picker shell + `connectorRegistry.ts`
- [x] Migrate stored P1 connections on read (`mssql_onprem` + `sql_login` default)
- [x] Per-connector React form stubs under `connections/connectors/` (§10)

**Exit criteria:** Factory returns adapters; flat fields removed; catalog endpoint drives Connect dialog.

### Phase P1.2 — Must-have auth (§7.2.2a)

- [x] `mssql_onprem` — `sql_login`, `windows_integrated`, `windows_login`
- [x] `azure_sql_database` — `sql_login`, `entra_service_principal`
- [x] `mysql` — `password` (+ optional SSL toggle)
- [x] `postgresql` — `password` + `sslmode` dropdown
- [x] `csv_s3_bucket` — `access_key` (`access_key_id`, `secret_access_key`)
- [x] Extended export — `auth_method`, `driver_options` (§7.2.10)
- [x] Update [sampleConfigfile.json](../docs/sampleConfigfile.json) + [INTEGRATION.md](../docs/INTEGRATION.md)
- [x] User-friendly connection error messages (driver/credential/network); full detail in API logs
- [ ] **script-generator contract sync** — parse P1.2 connection fields (`auth_method`, `driver_options`, `entra`, `access_key_id`, `secret_ref`); see §7.2.10 cross-product table and [script-generator REQUIREMENTS](../script-generator/docs/REQUIREMENTS.md) §9

**Exit criteria:** Tier P1.2 auth methods testable from API host; export matches extended contract. Script-generator can **validate** P1.2-shaped configs (compile may still use legacy `connection_string` until bootstrap auth work lands).

### Phase P1.3 — Azure Entra (should-have)

- [x] `azure_sql_database` — `entra_managed_identity`, `entra_password`
- [x] `postgresql` / `mysql` — Entra SP, MI, `entra_password` (Azure-hosted)
- [x] Export stores Entra non-secrets; migrator acquires tokens at run (OQ-21)

**Exit criteria:** Entra MI + password paths testable from API host (Azure credentials or configured local dev identity). Export `entra` block excludes secrets.

### Phase P1.4 — SSL/TLS + advanced S3 auth

- [x] `mysql` — full `ssl_mode` matrix (`password_ssl`)
- [x] `postgresql` — `password_ssl_client_cert`
- [x] `csv_s3_bucket` — `session_token`, `instance_profile`, `assume_role`
- [x] `mssql_onprem` — `ntlm` (if needed in target environments)

**Exit criteria:** Should-have auth tier complete per §7.2.2a.

### Phase P1.5 — `local_csv` connector

- [x] `LOCAL_CSV` export type + connector adapter
- [x] `local_path` — path field, allowlist, header sample test
- [x] `platform_staging` — `POST /connections/{ref}/files/upload` (500 MB cap, OQ-12)
- [x] `LocalCsvForm.tsx` in Connect UI
- [x] Staging cleanup on migration delete + 30-day TTL job

**Exit criteria:** Register path or upload under Connect; export `LOCAL_CSV` metadata only.

### Phase P1.6 — AWS RDS IAM

- [x] `mysql_rds_iam`, `postgresql_rds_iam` auth methods
- [x] Export intent only; migrator token acquisition documented

**Exit criteria:** RDS IAM auth testable; export consumable by migrator.

### Phase P2 — M0 + M2 + introspection

- [x] Migration CRUD API — `GET/POST/PUT/DELETE /migrations`
- [x] Blueprint sub-resources — add, delete, duplicate (deep copy), reorder
- [x] Full blueprint Pydantic model (sources, target, mappings, filters, chunking)
- [x] M0 UI — migration list, create dialog, header form
- [x] M2 UI — blueprint list with add / duplicate / delete / reorder
- [x] Introspection API — schemas, tables, columns, files
- [x] Introspection services — DB, S3, mock catalog
- [x] `SchemaTree` component (lazy DB tree + S3 file list)
- [x] Mock introspection dev flag — `CONFIG_API_USE_MOCK_INTROSPECTION`
- [x] API + web tests (migrations, factory, store)
- [x] Migration delete button in UI — `ConfigBuilderView` delete action
- [ ] `GET .../files/{name}/columns` — S3/local column sample preview
- [ ] Wire `SchemaTree` selection into blueprint JSON (deferred to P3 B1)

**Exit criteria:** Migration CRUD + schema tree; blueprint list editable. Wizard body editing is P3.

### Phase P3 — Blueprint wizard B1–B4

- [x] Wizard shell — `BlueprintWizard.tsx` + sidebar + Back/Next
- [x] Local step index draft (`useWizardStepIndex` / `useLocalDraft`)
- [ ] `StepSourcesJoins.tsx` (B1) — root table, joins, SchemaTree integration
- [ ] `StepTargetConflict.tsx` (B2) — target, PKs, all five `on_conflict` strategies
- [ ] `StepMappings.tsx` (B3) — derivations drawer + MUI X mapping grid
- [ ] `StepFiltersChunking.tsx` (B4) — pre/post filters, chunking toggle
- [ ] B5 Review — read-only blueprint summary (replace `WizardStepMock`)
- [ ] Bind wizard ↔ `MigrationRecord.blueprints[]` (load + save on step change)
- [ ] `SqlCodeEditor` component
- [ ] L1 validation on Next (§8); L2 debounced expression validate (P5 proxy can stub)

**Exit criteria:** Edit full single-blueprint JSON matching sample shape from wizard UI.

### Phase P3.5 — `LOCAL_CSV` wizard (pairs with P1.5)

- [ ] B1 file pickers — `connection_ref` + `file_name` for file-backed sources
- [ ] SchemaTree branch for `LOCAL_CSV` registered files + columns
- [ ] Sample column introspection wired (required for mapping grid, §7.1.4)
- [ ] Upload widget for `platform_staging` (depends on P1.5)

**Exit criteria:** CSV extract root/join selectable in B1; columns appear in SchemaTree.

### Phase P4 — Multi-blueprint export

- [x] Multi-blueprint storage + reorder (P2)
- [x] Per-connection export map — `GET /connections/export`
- [ ] `GET /migrations/{id}/export` — full migration JSON assembler
- [ ] Merge M0 header + `connections` + all `blueprints[]` → [sampleConfigfile.json](../docs/sampleConfigfile.json) shape
- [ ] Export preview / download UI (before P5 validate gate)

**Exit criteria:** Downloadable JSON with multiple blueprints matches contract file structure.

### Phase P5 — Review + validate proxy + JSON download

- [ ] `POST /migrations/{id}/validate` — proxy to script-generator
- [ ] Migration Review UI — full migration summary (all blueprints)
- [ ] L3 full validation before download (OQ-1)
- [ ] **Download JSON** disabled until validation passes
- [ ] Validation errors with `code`, `path`, `blueprint_sequence`

**Exit criteria:** Invalid configs cannot download; valid configs export clean JSON.

### Phase P6 — `unprocessed_table` + audit table

- [x] `unprocessed_table` field on blueprint model (API + types)
- [ ] `POST /connections/{ref}/tables/copy-structure` — create on target
- [ ] B2 UI — `IGNORE_AND_INSERT_UNPROCESSED` + **Create on target**
- [ ] B2 UI — `IGNORE_AND_LOG` audit table proposal + create (§12.4)

**Exit criteria:** B2 conflict flows complete for unprocessed + audit tables.

### Phase P7 — Generate SQL (optional)

- [ ] Generate SQL button on Review
- [ ] Proxy to script-generator compile API
- [ ] SQL artifact display / download

**Exit criteria:** One-click SQL from validated migration config.

### Phase P8 — Migrator handoff

- [x] Run nav placeholder — `MigrationRunnerView.tsx`
- [ ] **Open in Migrator** link from Review / export success
- [ ] `MIGRATOR_URL` deep link with `migration_id`

**Exit criteria:** Validated config hands off to migrator without shell rewrite.

### Phase P9 — Migrator file staging (cross-product)

- [ ] Migrator resolves `LOCAL_CSV` path / `staging_file_id` / S3 URI at run time
- [ ] Stream load per [executor-streaming-design.md](../script-generator/docs/executor-streaming-design.md)
- [ ] Pre-flight file-exists check before execute

**Exit criteria:** End-to-end CSV extract migration runs outside config platform.

### Phase P1.7+ — Edge connector auth (future)

- [ ] `gssapi` (PostgreSQL Kerberos)
- [ ] UNC credentials for `local_csv`
- [ ] MySQL client certificate auth
- [ ] `access_token` hook for API/CI only (OQ-22)

**Phase notes**

- **P1.5 vs P3.5:** **P1.5** = `local_csv` connector (Connect UI, test, export). **P3.5** = blueprint **B1** SchemaTree + file pickers. Same feature; two exit checks.
- **P3.5** can start after P3 B1 is in progress; migrator streaming (P9) can trail config export.
- **Recommended next build:** **P1.4** (SSL/TLS + advanced S3 auth) or **P3** (blueprint wizard B1–B4).

### 11.1 Phase summary (quick view)

| Phase | Status | Notes |
|-------|--------|-------|
| **P0** | [x] Complete | Shell, nav, sidebar wizard mock |
| **P1** | [x] Complete | Flat fields — refactor in P1.1 |
| **P1.1–P1.6** | [ ] In progress | P1.1–P1.3 complete; P1.4–P1.6 pending |
| **P2** | [x] Complete | Migration CRUD, introspection, M0/M2; wizard edit = P3 |
| **P3** | [ ] In progress | Shell + mocks only; B1–B4 forms pending |
| **P3.5** | [ ] Not started | `LOCAL_CSV` wizard wiring (after P1.5) |
| **P4–P9** | [ ] Not started | Export, validate, DDL, migrator handoff |

### 11.2 v1 sign-off checklist

**Status legend:** `[x]` = complete · `[ ]` = not started / in progress

- [ ] Six connectors with tiered auth per §7.2 (P1.1–P1.6)
- [x] Multiple blueprints per migration (add / duplicate / reorder / delete)
- [ ] Full blueprint wizard B1–B5 edits persisted to API
- [ ] `LOCAL_CSV` path + upload + wizard file pickers (P1.5 + P3.5)
- [ ] Export JSON matches [sampleConfigfile.json](../docs/sampleConfigfile.json)
- [ ] Validate-before-download enforced (OQ-1)
- [ ] All five `on_conflict` strategies in B2 UI
- [ ] Introspection for DB + S3 + local CSV sample columns
- [ ] Test connection required before save (all connectors)
- [ ] pytest + vitest pass; API never logs secrets

---

## 12. Decisions log

### 12.0 Summary table

| # | Topic | Decision | Status |
|---|--------|----------|--------|
| OQ-1 | Block download if invalid | **Yes** — Download disabled until full validation passes | Closed |
| OQ-2 | When to validate expressions | **Adopt recommendation:** L1 on Next; L2 on blur + on Next for B1/B3/B4; L3 before download | Closed |
| OQ-3 | Draft storage | **Both** — user chooses server and/or local | Closed |
| OQ-4 | UI component library | **MUI + MUI X Data Grid** (stakeholder confirmed) — §12.1 | Closed |
| OQ-5 | Blueprint step layout | **Sidebar (Layout B)** — stakeholder confirmed — §12.2 | Closed |
| OQ-6 | Duplicate blueprint | **Full deep copy** — §12.3 | Closed |
| OQ-7 | S3 introspection | **List files required**; header preview optional — §12.3 | Closed |
| OQ-8 | `IGNORE_AND_LOG` audit table | **Set structure from source/target context** — §12.4 | Closed |
| OQ-9 | Key Vault prep | **Optional nullable `secret_ref`** on API — §12.5 | Closed |
| OQ-10 | Auth / login | **No v1** — far future | Closed |
| OQ-11 | CSV file ingestion modes | **All three:** local path, S3, capped upload — §12.6 | Closed |
| OQ-12 | Upload size / retention | **500 MB default max**; **30-day TTL**; multi-GB → path/S3 — §12.6 | Closed |
| OQ-13 | File bytes in export JSON | **Never** — metadata references only — §12.6 | Closed |
| OQ-14 | XLSX file sources | **Deferred** after `LOCAL_CSV` v1 — §12.6 | Closed |
| OQ-15 | Connector registry vs flat fields | **`connector_id` + payload** — §7.2, §12.7 | Closed |
| OQ-16 | Azure SQL separate from on-prem MSSQL | **Yes** — `azure_sql_database` vs `mssql_onprem` — §12.7 | Closed |
| OQ-17 | Phase 1 auth breadth | **Tiered delivery P1.1–P1.7+** per §7.2.2a — not all auth in one release | Closed |
| OQ-18 | Export beyond `connection_string` | **`auth_method`, `driver_options`, `entra` block** — §7.2.10 | Closed |
| OQ-19 | UI: dynamic schema vs per-connector forms | **Per-connector React forms** — §12.7 | Closed |
| OQ-20 | Interactive Entra MFA in Connect UI | **Deferred** — use SP/MI/SQL auth (OQ-10 for interactive) — §12.7 | Closed |
| OQ-21 | Who acquires Entra/MI tokens at migration run | **Migrator** (config stores intent only) — §12.7 | Closed |
| OQ-22 | `access_token` in Azure SQL Connect UI | **Deferred** — API/CI only; no paste-token in UI — §12.7 | Closed |

### 12.1 UI library (OQ-4)

Pick one for `config-platform/web`. All are open source.

#### Option A — **MUI (Material UI)** + **MUI X Data Grid**

| Pros | Cons |
|------|------|
| Strong **data grid** for mapping matrix (sort, filter, column resize) | Heavier bundle |
| Tree View / third-party tree for **SchemaTree** | Material Design look (less unique) |
| Mature, widely used in **enterprise admin** tools | MUI X advanced grid features may need license for pro features (basic grid is OSS) |
| Good form components, validation patterns | — |
| Large docs and hiring pool | — |

**Best when:** Priority is dense tables, enterprise familiarity, fastest path to a complex mapping grid.

#### Option B — **shadcn/ui** + **Radix** + **Tailwind** + **TanStack Table**

| Pros | Cons |
|------|------|
| Modern, polished, highly **customizable** look | Mapping grid is **more DIY** (TanStack Table + custom cells) |
| Lighter, full control over CSS | More frontend assembly time |
| Radix = solid accessibility primitives | Schema tree = build or integrate (e.g. react-arborist) |
| No vendor lock-in (copy components into repo) | SQL editor still needs CodeMirror/Monaco either way |

**Best when:** Priority is distinctive UX and long-term UI ownership; team comfortable building grids.

#### Option C — **Ant Design**

| Pros | Cons |
|------|------|
| Excellent **Table** and **Form** for admin UIs | Strong visual identity (may feel “Ant” unless themed) |
| Tree, Steps, Modal patterns fit wizard well | Heavier; React 19 / strict mode quirks historically |
| Popular for data/ops tools | Less “western enterprise” default aesthetic |

**Best when:** You want wizard + tables fast with one coherent design system.

#### Recommendation for this project

**Primary recommendation: MUI + MUI X Data Grid** — the mapping grid and schema-heavy UI are the hardest parts; MUI X saves the most time for a data architect tool.

**Alternative:** shadcn + TanStack Table if you want a more custom product feel and accept more UI build time.

#### Decision (OQ-4) — **MUI + MUI X Data Grid** ✓ *Stakeholder confirmed*

**Why this fits now and later:**

| Future need | MUI path |
|-------------|----------|
| Mapping grid (100+ rows) | MUI X Data Grid — sort, filter, virtual scroll, inline edit |
| Database Studio / SQL scratchpad | Monaco or CodeMirror slots into MUI layout; `@mui/lab` / custom panels |
| Job Runner logs / streaming | `DataGrid` or virtualized `List` + `LinearProgress` |
| Validation anomaly matrix | Same grid patterns as mappings |
| Theming / white-label | MUI theme + `CssBaseline` — one design system for all nav modules |
| Accessibility | MUI WCAG baseline; less custom a11y work than fully DIY |
| Key Vault / auth later | Layout shell unchanged; add AppBar account menu when needed |

**Trade-off accepted:** Heavier bundle and Material look — acceptable for an internal/enterprise data tool where density and speed matter more than a marketing-site aesthetic.

**Stack for v1:** React 18+, TypeScript, MUI v6+, MUI X Data Grid (Community tier unless pro features required later).

**Revision policy:** Not a permanent lock — if a concrete blocker appears (licensing, grid limits, branding), revisit in a later phase; route/shell structure should not depend on MUI-specific APIs where avoidable.

---

### 12.2 Blueprint step layout (OQ-5)

Within one blueprint, steps B1–B4 can be laid out two ways. **P0 compared both**; sidebar (Layout B) was chosen (OQ-5).

#### Layout A — Horizontal tabs (top)

```text
┌─────────────────────────────────────────────────────────────────┐
│ Blueprint 2: billing_details          [Duplicate] [Delete]      │
├─────────────────────────────────────────────────────────────────┤
│  [1 Sources] [2 Target] [3 Mappings] [4 Filters]  [Review]      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    Active step content                          │
│                                                                 │
│                              [ Back ]  [ Next ]                 │
└─────────────────────────────────────────────────────────────────┘
```

| Pros | Cons |
|------|------|
| Familiar wizard pattern | Cramped on small screens with 4+ tabs |
| Clear “where am I” | Less room for step titles + help text |
| Good for linear first-time users | Harder to jump B1 ↔ B3 while debugging |

#### Layout B — Vertical sidebar (left)

```text
┌─────────────────────────────────────────────────────────────────┐
│ Blueprint 2: billing_details                                    │
├──────────────┬──────────────────────────────────────────────────┤
│ ● Sources    │                                                  │
│ ○ Target     │           Active step content                    │
│ ○ Mappings   │                                                  │
│ ○ Filters    │                                                  │
│ ○ Review     │                                                  │
│              │                    [ Back ]  [ Next ]           │
└──────────────┴──────────────────────────────────────────────────┘
```

| Pros | Cons |
|------|------|
| Easy jump between any step | Uses horizontal space |
| Scales to more steps later (e.g. GROUP BY) | Slightly less “wizard-like” for novices |
| Matches main app left nav pattern | — |
| Better for architects editing back and forth | — |

**Recommendation:** **Layout B (sidebar)** for this product — architects revisit sources and mappings often; consistency with global left nav.

#### Decision (OQ-5) — **Sidebar (Layout B)** ✓ *Stakeholder confirmed*

P0 compared Layout A (horizontal tabs) and Layout B (vertical sidebar). **Final:** sidebar for blueprint steps B1–B5 — matches app left nav; easy jump between Sources ↔ Mappings.

| Outcome | Detail |
|---------|--------|
| **Chosen** | `BlueprintWizardLayoutSidebar` — vertical step list + content pane |
| **Removed** | Tab layout prototype and dev toggle (not carried into P3) |
| **P3** | Real step forms plug into same sidebar shell (`BlueprintWizard`) |

---

### 12.3 Clarifications (OQ-6, OQ-7)

#### OQ-6 — What “Duplicate blueprint” means

You already have **Blueprint 1** (customers) configured. **Duplicate** creates **Blueprint 2** as a **full copy** of Blueprint 1’s sources, target, mappings, filters, and chunking — then you edit what changed.

| Option | Meaning |
|--------|---------|
| **Full copy (recommended)** | New `sequence_order`; clone all blueprint fields; user renames/adjusts |
| Connections-only copy | Only copies source graph — rarely useful |

**Example:** Duplicate billing blueprint to create a “billing archive” variant, then change S3 sources only.

**Recommendation:** **Full deep copy.** **Decision (OQ-6): Confirmed.**

#### OQ-7 — What “S3 introspection” means

For `CSV_S3_BUCKET` connections there is no SQL schema. Introspection means:

1. **List files** under the bucket URI prefix (e.g. `*.csv` in `s3://bucket/path/`).
2. User picks `file_name` for root or join (as in sample blueprint 3).
3. **Optional:** Preview first N rows / header row to suggest column names in SchemaTree (does not auto-write mappings).

**Recommendation:** **File listing required**; column preview **nice-to-have** in v1. **Decision (OQ-7): Confirmed.**

**Update (file sources, §7.1):** For `LOCAL_CSV`, **column preview from sample read is required** (mapping grid depends on it). S3 may keep optional preview until P3.5.

---

### 12.4 `IGNORE_AND_LOG` audit table (OQ-8)

**Decision:** Audit table name and structure are **derived from source and target context**, not a generic global default only.

**Default naming (editable):**

```text
{target_schema}.migration_conflict_{migration_id_short}_{blueprint_sequence}
```

**Suggested columns when creating on target:**

| Column | Purpose |
|--------|---------|
| `logged_at` | Timestamp |
| `migration_id` | From M0 |
| `blueprint_sequence` | Blueprint number |
| `target_schema`, `target_table` | Target identity |
| Primary key columns from `target.primary_keys` | Conflict row identity |
| `source_snapshot` | JSON or text — key source columns used in mapping (optional) |
| `reject_reason` | e.g. `DUPLICATE_KEY` |
| `raw_row` | Optional JSON of projected row |

Config export: engine today uses default `migration_conflict_log` unless extended — **config API may add optional `audit_table` on target in JSON when engine schema is extended**; until then UI documents the table DDL for manual creation or migrator-side setup.

UI flow: selecting `IGNORE_AND_LOG` shows proposed audit table + **Create on target** (same pattern as `unprocessed_table`).

---

### 12.5 Key Vault `secret_ref` (OQ-9) — explained

**Today:** Passwords live in exported JSON `connection_string` (your interim decision).

**Production:** Passwords live in **Azure Key Vault** (or similar); JSON stores a **reference**, not the secret.

**OQ-9 asks:** Should the API **reserve a field now** so we do not redesign later?

Example connection object (future-friendly):

```json
{
  "type": "MYSQL",
  "connection_string": "mysql://user:****@host:3306/db",
  "secret_ref": null
}
```

Later:

```json
"secret_ref": "keyvault://my-vault/secrets/crm-read-user"
```

| Reserve `secret_ref` now? | Pros | Cons |
|---------------------------|------|------|
| **Yes (recommended)** | No migration model break later; export can omit password when ref set | Slightly wider API model |
| No | Simpler v1 | Schema/API change when vault lands |

**Recommendation:** Add optional nullable `secret_ref` on API internal model; export still uses `connection_string` until vault integration. **Decision (OQ-9): Confirmed.**

---

### 12.6 File sources — CSV extracts (OQ-11–14)

#### OQ-11 — How architects attach CSV extracts

**Decision:** Support **three ingestion modes** with UI guidance by file size (§7.1.3):

| Mode | When to use |
|------|-------------|
| **Local / server path** | Huge files; API and migrator on same host or shared mount |
| **S3 (`CSV_S3_BUCKET`)** | Huge files; enterprise object storage |
| **Platform upload** | Small/medium files; hosted UI without S3 |

**Recommendation:** Default away from browser upload when file &gt; ~50 MB. **Decision (OQ-11): Confirmed.**

#### OQ-12 — Upload limits and retention

| Topic | Decision |
|-------|----------|
| Max upload size | **`CONFIG_API_MAX_UPLOAD_MB` default `500`** (override per environment) |
| Multi-GB | **No** naive full upload — require path or S3 |
| Resumable upload | Nice-to-have for Mode C; not blocking P3.5 MVP |
| Retention | Delete staging files on migration delete; **30-day TTL** on orphaned uploads |

**Decision (OQ-12): Confirmed.**

#### OQ-13 — File content in exported JSON

**Decision:** Exported config contains **references only** (`file_path`, `staging_file_id`, S3 URI, `file_name`, `parse_options`). **Never** embed CSV bytes in JSON. **Decision (OQ-13): Confirmed.**

#### OQ-14 — XLSX extracts

**Decision:** **Deferred.** Requires sheet selection, type inference, and run-time conversion (migrator or generator pre-step). Ship **`LOCAL_CSV` first**; add `LOCAL_XLSX` in a later phase. **Decision (OQ-14): Confirmed.**

#### End-to-end workflow (CSV extract → migration)

1. **Register file source** under Connect (path, S3, or upload).
2. **Verify & save** — API checks access and parses header sample.
3. **Create/open migration** → blueprint B1: root/join = file connection + `file_name`.
4. **B2–B4** — target DB introspection and mappings as today.
5. **Review & export** JSON (metadata only).
6. **Migrator** resolves file, streams stage, runs generated SQL (P9).

---

### 12.7 Connection connectors & DB authentication (OQ-15–22)

#### OQ-15 — Replace flat database fields with connector registry

**Decision:** Saved connections use **`connector_id` + `connector_payload`**. `ConnectorRegistry` (factory) returns adapter implementing validate, fingerprint, test, export, introspection. **Decision (OQ-15): Confirmed.**

#### OQ-16 — On-prem SQL Server vs Azure SQL Database

**Decision:** **Separate connectors** — `mssql_onprem` and `azure_sql_database` (ADB). Different defaults, auth options, and export driver options. Export `type` may both be `MSSQL`. **Decision (OQ-16): Confirmed.**

#### OQ-17 — Phase 1 connector and auth coverage

**Decision:** Six connectors (§7.2.2) with auth methods in §7.2.3–7.2.8, delivered in **tiers** (§7.2.2a, §7.2.12) — not a single big-bang release:

| Tier | Phases | Summary |
|------|--------|---------|
| **Must-have** | P1.1–P1.2 | SQL/Windows MSSQL; Azure SQL SQL + Entra SP; MySQL/Postgres password; S3 access key |
| **Should-have** | P1.3–P1.4 | Entra MI/password; full SSL; S3 roles; `ntlm` |
| **File** | P1.5 + P3.5 | `local_csv` connector + wizard wiring |
| **AWS RDS IAM** | P1.6 | `mysql_rds_iam`, `postgresql_rds_iam` |
| **Edge** | P1.7+ | `gssapi`, UNC creds, `access_token` API hook |

**Decision (OQ-17): Confirmed** (amended for tiered delivery).

#### OQ-18 — Extended export contract

**Decision:** Export includes `auth_method`, `driver_options`, and connector-specific non-secret blocks (e.g. `entra.tenant_id`) in addition to `connection_string` / S3 / file refs. **Decision (OQ-18): Confirmed.**

#### OQ-19 — UI form strategy

**Decision:** **One form component per `connector_id`** with internal branching on `auth_method` (not a single generic host/user/password form). **Decision (OQ-19): Confirmed.**

#### OQ-20 — Interactive Entra (MFA) in connection dialog

**Decision:** **Not Phase 1 Connect UI.** Requires platform-level user sign-in (OQ-10) or OAuth redirect. Phase 1 uses SQL auth, service principal, and managed identity — not interactive MFA or paste-token (OQ-22). **Decision (OQ-20): Confirmed.**

#### OQ-21 — Token acquisition at migration run

**Decision:** Config platform **tests** connectivity at save time but exported JSON does **not** store long-lived Entra/AWS tokens. **Migrator** (or execution host) acquires fresh tokens for `entra_*`, `instance_profile`, and `assume_role` at run time using `auth_method` + `secret_ref`. **Decision (OQ-21): Confirmed.**

#### OQ-22 — `access_token` (Azure SQL) in Connect UI

**Decision:** **Not in Connect UI** for Phase 1. Short-lived supplied tokens are discouraged (security, fingerprint, UX). Supported later for **API/CI automation only** if needed. Phase 1 Azure SQL UI: `sql_login`, `entra_service_principal` (P1.2); `entra_managed_identity`, `entra_password` (P1.3). **Decision (OQ-22): Confirmed.**

---

## 13. Recommendations summary

1. **Multiple blueprints per migration** in v1 — required for real configs.  
2. **Migration header (M0)** for `migration_id`, `client_id`, `version`.  
3. **Job Runner** stays a shell placeholder; execution and custom `.sql` belong to **migrator**.  
4. **Connector registry** (`connector_id` + payload) + assembled export per §7.2 (replaces single generic DB form).  
5. **Introspection required** for target, SQL sources, and file sources (`LOCAL_CSV` sample columns; S3 file list).  
6. **All five** `on_conflict` strategies + `unprocessed_table` with create-on-target.  
7. **Validate before download**; layered L1/L2/L3 validation.  
8. **MySQL compile dialect** shown explicitly in UI.  
9. **No** blueprint custom-SQL override; **no** `fallback_value`; **no** GROUP BY UI in v1.  
10. Shell registers **all nav slots** in P0 so Run/Studio/Validation plug in later.  
11. **Download blocked** until full validation (OQ-1).  
12. **Dual draft storage** — server and local, user choice (OQ-3).  
13. **`IGNORE_AND_LOG`** audit table structure derived from target/source (OQ-8).  
14. **Auth deferred** to far future (OQ-10).  
15. **MUI + MUI X** for UI (OQ-4); **sidebar** blueprint step layout (OQ-5).  
16. **Duplicate blueprint** = full deep copy (OQ-6).  
17. **S3:** list files + optional header preview (OQ-7); **`LOCAL_CSV`** sample column preview required (§7.1).  
18. **`secret_ref`** reserved on API for Key Vault (OQ-9).  
19. **Web-first deployment**; optional local stack or desktop shell later; migrator owns execution-side desktop (§1.4).  
20. **CSV file sources:** three ingestion modes; design-time sample only; migrator streams full file (OQ-11, OQ-13).  
21. **Upload defaults:** 500 MB max, 30-day staging TTL (OQ-12).  
22. **Six connectors** with **tiered auth delivery** P1.1–P1.7+ (§7.2.2a; OQ-17).  
23. **P1.2 must-have:** on-prem MSSQL SQL + Windows; Azure SQL SQL + Entra SP; MySQL/Postgres password; S3 access key.  
24. **P1.3–P1.4:** Entra MI/password, SSL depth, S3 role auth; **`access_token` not in UI** (OQ-22).  
25. **P1.5 + P3.5:** `local_csv` connector + wizard file UX (not P1.2).  
26. **P1.6:** AWS RDS IAM for MySQL/Postgres.  
27. **Export** extended with `auth_method` + `driver_options`; migrator acquires tokens at run (OQ-18, OQ-21).  
28. **Contract follow-up:** When P1.2 export lands, update [sampleConfigfile.json](../docs/sampleConfigfile.json), [INTEGRATION.md](../docs/INTEGRATION.md), and **script-generator** connection models so P1.2 fields parse (minimum); full `auth_method` use in bootstrap and migrator token acquisition is a later phase (§7.2.10).

---

## 14. Related documents

| Document | Purpose | Sync when |
|----------|---------|-----------|
| [codeSanityInstructionsToAI.md](codeSanityInstructionsToAI.md) | AI / dev quality bar for this repo | When conventions change |
| [../docs/INTEGRATION.md](../docs/INTEGRATION.md) | HTTP contracts between products | P1.2 export, P5 validate |
| [../docs/sampleConfigfile.json](../docs/sampleConfigfile.json) | Config contract example | P1.2 (`LOCAL_CSV`, `auth_method`), P3.5 |
| [../script-generator/docs/REQUIREMENTS.md](../script-generator/docs/REQUIREMENTS.md) | SQL generator spec | P1.2 auth export, P5 validate |
