# Migration Engine

Configuration-driven, multi-tenant ELT migration tool. Phase 1 delivers JSON blueprint parsing and validation.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Validate a config

```bash
py -m migration_engine validate --config docs/sampleConfigfile.json
```

## Run tests

```bash
pytest
```

## Project layout

See [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) for the full specification and implementation phases.
