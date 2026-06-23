# Integration — How the Products Connect

Cross-product contracts for the **Data Migration Platform**. Product-specific design lives in each product folder under `docs/`.

---

## Products

| Product | Folder | Input | Output |
|---------|--------|--------|--------|
| **Config platform** | `config-platform/` | UI user input | Migration config file |
| **Script generator** | `script-generator/` | Migration config | Migration script (SQL today) |
| **Migrator** | `migrator/` | Migration script + target | Executed migration |

```text
config-platform          script-generator           migrator
     │                         │                       │
     │  config file (JSON)     │  SQL script           │
     └────────────────────────►└──────────────────────► target DB
```

Each product is a **separate application** with its own build and deploy. Communication is **HTTP APIs** and/or **shared files** — not shared Python/React imports across product folders.

---

## Shared contract: migration config

- **Reference file:** [sampleConfigfile.json](sampleConfigfile.json)
- **Format today:** JSON
- **Format future:** Additional formats via config parser factory (YAML, etc.)

Config platform **produces** this file. Script generator **consumes** it.

---

## Script generator API (planned)

Base URL example: `http://localhost:8001`

| Method | Path | Request | Response |
|--------|------|---------|----------|
| `POST` | `/validate` | Migration config JSON body | Validation report JSON |
| `POST` | `/generate` | Migration config JSON body | SQL script text or file download |

Config platform calls these endpoints when the user requests validation or SQL generation. The generator does not store drafts or user sessions.

**CLI today** (same logic, local use):

```bash
cd script-generator
py -m migration_engine validate --config ../docs/sampleConfigfile.json
py -m migration_engine generate --config ../docs/sampleConfigfile.json --output output/migration.sql
```

---

## Config platform API (planned)

Base URL example: `http://localhost:8000`

| Area | Purpose |
|------|---------|
| Blueprint CRUD | Save/load draft migrations per client |
| Export | Download config JSON matching shared contract |
| Proxy | Forward validate/generate to script generator API |

Frontend (`config-platform/web/`) talks **only** to config API — never directly to script generator or migrator.

---

## Migrator API (planned)

Base URL example: `http://localhost:8002`

| Method | Path | Request | Response |
|--------|------|---------|----------|
| `POST` | `/execute` | SQL script + target connection ref | Execution report (rows, errors, status) |

Input is the **output of script generator**. Migrator does not compile configs or serve UI.

---

## Environment variables (local dev)

```text
CONFIG_PLATFORM_API_URL=http://localhost:8000
SCRIPT_GENERATOR_URL=http://localhost:8001
MIGRATOR_URL=http://localhost:8002
```

---

## Extensibility

| Axis | Today | Extension mechanism |
|------|--------|---------------------|
| Config format | JSON | Config parser factory in each consumer |
| Generated artifact | SQL | `ScriptGeneratorFactory` / output format registry |
| Compile dialect | MySQL | `DialectFactory` |
| Target execution | MySQL script run | Migrator adapters + executor |

---

## Future repo split

Because integration is HTTP + config file contract, any folder can become its own repository by:

1. Moving the folder to a new remote
2. Updating service URLs in environment config
3. Keeping [sampleConfigfile.json](sampleConfigfile.json) (or published schema) as the shared contract

No compiler or UI code changes required.

---

## Related documentation

| Document | Location |
|----------|----------|
| Platform overview | [../README.md](../README.md) |
| Script generator architecture | [../script-generator/docs/ARCHITECTURE.md](../script-generator/docs/ARCHITECTURE.md) |
| Script generator requirements | [../script-generator/docs/REQUIREMENTS.md](../script-generator/docs/REQUIREMENTS.md) |

Config platform and migrator `docs/` folders will be added when those products are implemented.
