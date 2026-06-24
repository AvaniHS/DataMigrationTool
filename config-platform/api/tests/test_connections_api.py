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
        "connector_id": "mysql",
        "connector_payload": {
            "auth_method": "password",
            "host": "client-crm-ip",
            "port": 3306,
            "database": "crm_db",
            "username": "read_user",
            "password": "pass",
            "use_advanced_string": False,
        },
    }


def test_list_connectors_catalog(client: TestClient) -> None:
    response = client.get("/connectors")
    assert response.status_code == 200
    connector_ids = {item["connector_id"] for item in response.json()}
    assert "mysql" in connector_ids
    assert "local_csv" in connector_ids


def test_create_requires_successful_test(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "config_platform_api.routers.connections.test_connection",
        lambda _request: type("Result", (), {"success": True, "message": "ok"})(),
    )

    test_response = client.post(
        "/connections/test",
        json={
            "connector_id": "mysql",
            "connector_payload": _mysql_payload()["connector_payload"],
        },
    )
    assert test_response.status_code == 200
    token = test_response.json()["verification_token"]

    save_body = {**_mysql_payload(), "verification_token": token}
    create_response = client.post("/connections", json=save_body)
    assert create_response.status_code == 201
    body = create_response.json()
    assert body["ref"] == "client_crm_mysql"
    assert body["connector_id"] == "mysql"


def test_create_rejects_missing_verification_token(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "config_platform_api.routers.connections.test_connection",
        lambda _request: type("Result", (), {"success": True, "message": "ok"})(),
    )
    test_response = client.post(
        "/connections/test",
        json={
            "connector_id": "mysql",
            "connector_payload": _mysql_payload()["connector_payload"],
        },
    )
    token = test_response.json()["verification_token"]

    tampered = _mysql_payload()
    tampered["connector_payload"] = {
        **tampered["connector_payload"],  # type: ignore[dict-item]
        "password": "different",
    }
    tampered["verification_token"] = token
    create_response = client.post("/connections", json=tampered)
    assert create_response.status_code == 400


def test_export_matches_contract(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "config_platform_api.routers.connections.test_connection",
        lambda _request: type("Result", (), {"success": True, "message": "ok"})(),
    )
    test_response = client.post(
        "/connections/test",
        json={
            "connector_id": "mysql",
            "connector_payload": _mysql_payload()["connector_payload"],
        },
    )
    token = test_response.json()["verification_token"]
    client.post("/connections", json={**_mysql_payload(), "verification_token": token})

    export_response = client.get("/connections/export")
    assert export_response.status_code == 200
    exported = export_response.json()["client_crm_mysql"]
    assert exported["type"] == "MYSQL"
    assert exported["connection_string"] == "mysql://read_user:pass@client-crm-ip:3306/crm_db"
