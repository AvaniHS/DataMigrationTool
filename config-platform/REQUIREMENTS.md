# Config Platform — Requirements (v1 Draft)

**Status:** §12 decisions complete except final layout pick after P0 prototype (OQ-5)  
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
| Blueprint step layout | **Prototype both** tabs + sidebar in P0; pick winner before P3 (OQ-5) |
| Duplicate blueprint | **Full deep copy** (OQ-6) |
| S3 introspection | **File listing required**; column header preview optional in v1 (OQ-7) |
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
│  Data Onboarding Toolkit                                               │
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

- Types: `MYSQL`, `MSSQL`, `POSTGRESQL`, `CSV_S3_BUCKET`
- Dynamic forms per type
- **Test connection required** before Save
- Saved entries populate top-level `connections` map

See [§7 Connection storage](#7-connection-storage-recommendation).

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

### 6.1 Connections (M1)

1. Render `connections` registry; empty state → **Add connection**.
2. Modal: select type → dynamic fields (see §7).
3. **Test connection** (required) → success/failure UI.
4. **Save** → store under connection key (`connection_ref` name).
5. Auto-open from wizard if blueprint references missing connection.

### 6.2 Blueprint B1 — Sources & joins

1. **Left pane:** `SchemaTree` + connection switcher.
2. Introspection API loads schemas → tables → columns for selected connection.
3. **Right pane:** Source graph canvas.
4. **Set as root table** → `sources.root_table` (alias, schema, table or `file_name` for S3).
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

### Option A — Structured fields (recommended for v1)

UI stores: `host`, `port`, `database`, `username`, `password` (+ S3: `s3_bucket_uri`, `aws_region`).

Config API **assembles** `connection_string` on export to match engine contract.

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

**Open for your confirmation:** See [§12 Open questions](#12-open-questions).

---

## 9. Config API (FastAPI) — responsibilities

| Area | Endpoints (illustrative) | Notes |
|------|--------------------------|-------|
| Migrations CRUD | `GET/POST/PUT /migrations` | Draft storage (DB TBD) |
| Connections | `POST /connections/test` | Required before save |
| Metadata | `GET /connections/{ref}/schemas`, `.../tables`, `.../columns` | Introspection |
| Target DDL | `POST /connections/{ref}/tables/copy-structure` | For `unprocessed_table` |
| Export | `GET /migrations/{id}/export` | Produces contract JSON |
| Validate proxy | `POST /migrations/{id}/validate` | Forwards to script-generator |

Frontend **never** calls script-generator directly (per [INTEGRATION.md](../docs/INTEGRATION.md)).

### FastAPI concerns (brief)

| Concern | Mitigation |
|---------|------------|
| Credential handling | Never log passwords; HTTPS only; prepare for Key Vault |
| SQL injection in introspection | Parameterized metadata queries only |
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
        │   ├── shared/
        │   │   ├── SchemaTree.tsx
        │   │   └── SqlCodeEditor.tsx
        │   └── config_wizard/
        │       ├── MigrationHeaderForm.tsx    # M0
        │       ├── BlueprintList.tsx            # M2
        │       ├── WizardContainer.tsx
        │       ├── StepSourcesJoins.tsx         # B1
        │       ├── StepTargetConflict.tsx       # B2
        │       ├── StepMappings.tsx             # B3
        │       └── StepFiltersChunking.tsx      # B4
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

## 11. Implementation phases

| Phase | Scope | Exit criteria |
|-------|--------|---------------|
| **P0** | Shell + routes + placeholders; **prototype both** blueprint layouts (tabs + sidebar) | Nav works; layout A/B comparable in Storybook or dev toggle |
| **P1** | Connections + test + structured export strings | All connection types testable |
| **P2** | M0 + M2 + introspection APIs | Migration CRUD + schema tree |
| **P3** | Blueprint wizard B1–B4 | Edit full blueprint matching sample |
| **P4** | Multi-blueprint + reorder | Export matches multi-blueprint sample |
| **P5** | Review + validate proxy + JSON download | Invalid configs cannot download |
| **P6** | `unprocessed_table` create-on-target | B2 flow complete for IGNORE_AND_INSERT_UNPROCESSED |
| **P7** | Generate SQL button (optional) | Proxy to script-generator |
| **P8** | Migrator handoff link | “Open in Migrator” from review |

---

## 12. Decisions log (open questions)

### 12.0 Summary table

| # | Topic | Decision | Status |
|---|--------|----------|--------|
| OQ-1 | Block download if invalid | **Yes** — Download disabled until full validation passes | Closed |
| OQ-2 | When to validate expressions | **Adopt recommendation:** L1 on Next; L2 on blur + on Next for B1/B3/B4; L3 before download | Closed |
| OQ-3 | Draft storage | **Both** — user chooses server and/or local | Closed |
| OQ-4 | UI component library | **MUI + MUI X Data Grid** (stakeholder confirmed) — §12.1 | Closed |
| OQ-5 | Blueprint step layout | **Prototype both** in P0; choose before P3 — §12.2 | In progress |
| OQ-6 | Duplicate blueprint | **Full deep copy** — §12.3 | Closed |
| OQ-7 | S3 introspection | **List files required**; header preview optional — §12.3 | Closed |
| OQ-8 | `IGNORE_AND_LOG` audit table | **Set structure from source/target context** — §12.4 | Closed |
| OQ-9 | Key Vault prep | **Optional nullable `secret_ref`** on API — §12.5 | Closed |
| OQ-10 | Auth / login | **No v1** — far future | Closed |

---

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

Within one blueprint, steps B1–B4 can be laid out two ways. **P0 prototype should implement both as toggles or storybook views** so you can compare.

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

#### Decision (OQ-5) — **Prototype both in P0**

| Deliverable | Purpose |
|-------------|---------|
| Layout A (tabs) + Layout B (sidebar) | Same mock step content; switch via Storybook or dev flag |
| User review | Pick one before **P3** (real wizard implementation) |
| Fallback | If undecided, default to **sidebar** for P3 |

**Exit criterion for P0:** Stakeholder signs off on A or B (or hybrid: sidebar on desktop, tabs on narrow viewport — optional).

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

## 13. Recommendations summary

1. **Multiple blueprints per migration** in v1 — required for real configs.  
2. **Migration header (M0)** for `migration_id`, `client_id`, `version`.  
3. **Job Runner** stays a shell placeholder; execution and custom `.sql` belong to **migrator**.  
4. **Structured connection fields** + assembled `connection_string` on export.  
5. **Introspection required** for target and SQL sources.  
6. **All five** `on_conflict` strategies + `unprocessed_table` with create-on-target.  
7. **Validate before download**; layered L1/L2/L3 validation.  
8. **MySQL compile dialect** shown explicitly in UI.  
9. **No** blueprint custom-SQL override; **no** `fallback_value`; **no** GROUP BY UI in v1.  
10. Shell registers **all nav slots** in P0 so Run/Studio/Validation plug in later.  
11. **Download blocked** until full validation (OQ-1).  
12. **Dual draft storage** — server and local, user choice (OQ-3).  
13. **`IGNORE_AND_LOG`** audit table structure derived from target/source (OQ-8).  
14. **Auth deferred** to far future (OQ-10).  
15. **MUI + MUI X** for UI (OQ-4); **prototype both** blueprint layouts in P0 (OQ-5).  
16. **Duplicate blueprint** = full deep copy (OQ-6).  
17. **S3:** list files + optional header preview (OQ-7).  
18. **`secret_ref`** reserved on API for Key Vault (OQ-9).  
19. **Web-first deployment**; optional local stack or desktop shell later; migrator owns execution-side desktop (§1.4).

---

## 14. Related documents

| Document | Purpose |
|----------|---------|
| [REQUIREMENTS.md](REQUIREMENTS.md) | Original raw UI ideas (archived in git history) |
| [../docs/INTEGRATION.md](../docs/INTEGRATION.md) | HTTP contracts between products |
| [../docs/sampleConfigfile.json](../docs/sampleConfigfile.json) | Config contract example |
| [../script-generator/docs/REQUIREMENTS.md](../script-generator/docs/REQUIREMENTS.md) | SQL generator spec |
