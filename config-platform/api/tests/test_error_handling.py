import json
from pathlib import Path

from fastapi.testclient import TestClient

from config_platform_api.dependencies import get_connection_store
from config_platform_api.main import app
from config_platform_api.storage.connection_store import ConnectionStore


def test_corrupt_connection_store_returns_500(tmp_path: Path) -> None:
    storage_path = tmp_path / "connections.json"
    storage_path.write_text("{not-valid-json", encoding="utf-8")
    store = ConnectionStore(storage_path)
    app.dependency_overrides[get_connection_store] = lambda: store

    try:
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/connections")
        assert response.status_code == 500
        assert response.json()["detail"] == "Connection registry is unavailable."
    finally:
        app.dependency_overrides.clear()


def test_connection_validation_error_returns_422() -> None:
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/connections/test",
        json={"connector_id": "mysql", "connector_payload": {"auth_method": "password"}},
    )
    assert response.status_code == 422
