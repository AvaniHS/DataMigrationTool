# Config platform API

```bash
cd config-platform/api
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn config_platform_api.main:app --reload --port 8000
```
