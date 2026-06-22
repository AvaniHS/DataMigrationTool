# Migration Engine

Configuration-driven, multi-tenant ELT migration tool that turns JSON blueprints into runnable MySQL SQL scripts.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Validate a config

```bash
py -m migration_engine validate --config docs/sampleConfigfile.json
py -m migration_engine validate --config docs/sampleConfigfile.json --dialect MYSQL
```

## Generate SQL

```bash
py -m migration_engine generate --config docs/sampleConfigfile.json --output output/migration.sql
py -m migration_engine generate --config docs/sampleConfigfile.json --output output/migration.sql --dialect MYSQL
```

The `generate` command validates the config first, then writes a self-contained script with:

- Source bootstrap preambles for MySQL, MSSQL, PostgreSQL, and S3 CSV sources
- CTE pipeline per blueprint
- Chunking loop for large blueprints (when enabled)
- Per-blueprint transaction and savepoint boundaries

## Run tests

```bash
pytest
```

## Project layout

See [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) for the full specification and implementation phases.

Source bootstrap patterns: [docs/source-bootstrap-patterns.md](docs/source-bootstrap-patterns.md)
