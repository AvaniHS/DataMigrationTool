# Config platform API

```bash
cd config-platform/api
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn config_platform_api.main:app --reload --port 8000
```

Connections API (P1): `GET/POST/PUT/DELETE /connections`, `POST /connections/test`, `GET /connections/export`
