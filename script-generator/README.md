# Script Generator

Validates migration config and generates SQL scripts.

**Input:** migration config file (JSON today)  
**Output:** SQL script (MySQL today)

## Setup

```bash
cd script-generator
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## Commands

```bash
py -m migration_engine validate --config ../docs/sampleConfigfile.json
py -m migration_engine generate --config ../docs/sampleConfigfile.json --output output/migration.sql
pytest
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Compiler design and patterns |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | Functional spec and phases |
| [../docs/INTEGRATION.md](../docs/INTEGRATION.md) | How products connect |

Platform overview: [../README.md](../README.md)
