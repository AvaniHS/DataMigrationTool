# Data Migration Platform

Three independent applications for migration **authoring**, **script generation**, and **execution**.

| Product | Folder | Input → Output | Status |
|---------|--------|----------------|--------|
| **Config platform** | `config-platform/` | UI input → config file | Planned |
| **Script generator** | `script-generator/` | Config → SQL script | **Active** |
| **Migrator** | `migrator/` | SQL script → target DB migration | Planned |

```text
config-platform  ──►  script-generator  ──►  migrator
   (config file)         (SQL file)           (run)
```

**Integration:** [docs/INTEGRATION.md](docs/INTEGRATION.md) — HTTP APIs and shared config contract.

---

## Repository layout

```text
DataMigrationTool/
├── README.md                 ← platform entry (this file)
├── docs/
│   ├── INTEGRATION.md        ← cross-product contracts
│   └── sampleConfigfile.json ← shared config example
├── script-generator/         ← Product 1 (implemented)
│   ├── docs/                 ← generator architecture & requirements
│   ├── src/migration_engine/
│   └── tests/
├── config-platform/
│   ├── api/                  ← backend (placeholder)
│   └── web/                  ← frontend (placeholder)
└── migrator/                 ← executor (placeholder)
```

---

## Quick start — script generator

```bash
cd script-generator
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

```bash
py -m migration_engine validate --config ../docs/sampleConfigfile.json
py -m migration_engine generate --config ../docs/sampleConfigfile.json --output output/migration.sql
pytest
```

Sample config: [docs/sampleConfigfile.json](docs/sampleConfigfile.json)

---

## Documentation

| Document | Scope |
|----------|--------|
| [docs/INTEGRATION.md](docs/INTEGRATION.md) | APIs and contracts between products |
| [script-generator/README.md](script-generator/README.md) | Run generator, local commands |
| [config-platform/REQUIREMENTS.md](config-platform/REQUIREMENTS.md) | Config UI/API v1 draft |
| [script-generator/docs/ARCHITECTURE.md](script-generator/docs/ARCHITECTURE.md) | Generator design and patterns |
| [script-generator/docs/REQUIREMENTS.md](script-generator/docs/REQUIREMENTS.md) | Generator spec and phases |

Config platform and migrator docs will be added under their folders when development starts.

---

## Implementation status

| Step | Description | Status |
|------|-------------|--------|
| 1 | Three-product folder split | Done |
| 2 | `docs/INTEGRATION.md` | Done |
| 3 | Script generator HTTP API | Planned |
| 4 | Config platform (api + web) | Planned |
| 5 | Migrator | Planned |
