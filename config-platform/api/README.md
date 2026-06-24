# Config platform API

```bash
cd config-platform/api
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn config_platform_api.main:app --reload --port 8000
```

Connections API (P1): `GET/POST/PUT/DELETE /connections`, `POST /connections/test`, `GET /connections/export`

### Local CSV (`local_path`)

The API only reads files under **allowlisted directories** (default: `data/` next to this folder). If test fails with "outside allowed roots":

1. **Easiest:** put the CSV under `config-platform/api/data/` and use e.g. `data/myfile.csv`, or use **Platform upload** in the Connect UI.
2. **Custom roots:** copy `.env.example` to `.env` and set `CONFIG_API_FILE_ROOTS` to a JSON array of parent folders, then restart uvicorn.

```env
CONFIG_API_FILE_ROOTS=["data","D:/Projects/TL/Projects/DataMigrationTool/docs"]
```
