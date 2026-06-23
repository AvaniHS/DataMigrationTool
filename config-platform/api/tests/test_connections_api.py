from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from config_platform_api.dependencies import get_connection_store, get_verification_store
from config_platform_api.main import app
from config_platform_api.services.verification_store import VerificationStore
from config_platform_api.storage.connection_store import ConnectionStore


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    store = ConnectionStore(tmp_path / "connections.json")
    verification = VerificationStore(ttl_seconds=900)
    app.dependency_overrides[get_connection_store] = lambda: store
    app.dependency_overrides[get_verification_store] = lambda: verification
    yield TestClient(app)
    app.dependency_overrides.clear()


def _mysql_payload(ref: str = "client_crm_mysql") -> dict[str, object]:
    return {
        "ref": ref,
        "type": "MYSQL",
        "database": {
            "host": "client-crm-ip",
            "port": 3306,
            "database": "crm_db",
            "username": "read_user",
            "password": "pass",
            "use_advanced_string": False,
        },
    }


def test_create_requires_successful_test(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "config_platform_api.routers.connections.test_connection",
        lambda _request: type("Result", (), {"success": True, "message": "ok"})(),
    )

    test_response = client.post("/connections/test", json={"type": "MYSQL", "database": _mysql_payload()["database"]})
    assert test_response.status_code == 200
    token = test_response.json()["verification_token"]

    save_body = {**_mysql_payload(), "verification_token": token}
    create_response = client.post("/connections", json=save_body)
    assert create_response.status_code == 201
    assert create_response.json()["ref"] == "client_crm_mysql"


def test_create_rejects_missing_verification_token(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "config_platform_api.routers.connections.test_connection",
        lambda _request: type("Result", (), {"success": True, "message": "ok"})(),
    )
    test_response = client.post("/connections/test", json={"type": "MYSQL", "database": _mysql_payload()["database"]})
    token = test_response.json()["verification_token"]

    tampered = _mysql_payload()
    tampered["database"] = {**tampered["database"], "password": "different"}  # type: ignore[dict-item]
    tampered["verification_token"] = token
    create_response = client.post("/connections", json=tampered)
    assert create_response.status_code == 400


def test_export_matches_contract(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "config_platform_api.routers.connections.test_connection",
        lambda _request: type("Result", (), {"success": True, "message": "ok"})(),
    )
    test_response = client.post("/connections/test", json={"type": "MYSQL", "database": _mysql_payload()["database"]})
    token = test_response.json()["verification_token"]
    client.post("/connections", json={**_mysql_payload(), "verification_token": token})

    export_response = client.get("/connections/export")
    assert export_response.status_code == 200
    exported = export_response.json()["client_crm_mysql"]
    assert exported["type"] == "MYSQL"
    assert exported["connection_string"] == "mysql://read_user:pass@client-crm-ip:3306/crm_db"
