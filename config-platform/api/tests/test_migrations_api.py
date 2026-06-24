from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from config_platform_api.dependencies import get_connection_store, get_migration_store, get_verification_store
from config_platform_api.main import app
from config_platform_api.services.verification_store import VerificationStore
from config_platform_api.storage.connection_store import ConnectionStore
from config_platform_api.storage.migration_store import MigrationStore


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("CONFIG_API_USE_MOCK_INTROSPECTION", "true")

    connection_store = ConnectionStore(tmp_path / "connections.json")
    migration_store = MigrationStore(tmp_path / "migrations.json")
    verification = VerificationStore(ttl_seconds=900)
    app.dependency_overrides[get_connection_store] = lambda: connection_store
    app.dependency_overrides[get_migration_store] = lambda: migration_store
    app.dependency_overrides[get_verification_store] = lambda: verification
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_migration_crud_and_blueprint_actions(client: TestClient) -> None:
    create_response = client.post(
        "/migrations",
        json={
            "migration_id": "mig_test_2026",
            "client_id": "client_acme",
            "version": "1.0.0",
            "output_format": "SQL",
        },
    )
    assert create_response.status_code == 201
    assert create_response.json()["blueprints"] == []

    list_response = client.get("/migrations")
    assert list_response.status_code == 200
    assert list_response.json()[0]["blueprint_count"] == 0

    add_blueprint = client.post("/migrations/mig_test_2026/blueprints")
    assert add_blueprint.status_code == 200
    assert len(add_blueprint.json()["blueprints"]) == 1

    duplicate = client.post("/migrations/mig_test_2026/blueprints/1/duplicate")
    assert duplicate.status_code == 200
    assert len(duplicate.json()["blueprints"]) == 2

    reorder = client.put(
        "/migrations/mig_test_2026/blueprints/reorder",
        json={"sequence_orders": [2, 1]},
    )
    assert reorder.status_code == 200
    assert [bp["sequence_order"] for bp in reorder.json()["blueprints"]] == [1, 2]

    delete_blueprint = client.delete("/migrations/mig_test_2026/blueprints/2")
    assert delete_blueprint.status_code == 200
    assert len(delete_blueprint.json()["blueprints"]) == 1

    update = client.put(
        "/migrations/mig_test_2026",
        json={
            "client_id": "client_acme_updated",
            "version": "1.1.0",
            "blueprints": delete_blueprint.json()["blueprints"],
        },
    )
    assert update.status_code == 200
    assert update.json()["client_id"] == "client_acme_updated"

    delete_migration = client.delete("/migrations/mig_test_2026")
    assert delete_migration.status_code == 204


def test_mock_introspection_endpoints(client: TestClient) -> None:
    schemas = client.get("/connections/any_ref/schemas")
    assert schemas.status_code == 200
    assert any(item["name"] == "crm_db" for item in schemas.json())

    tables = client.get("/connections/any_ref/schemas/crm_db/tables")
    assert tables.status_code == 200
    assert any(item["name"] == "customer_master" for item in tables.json())

    columns = client.get("/connections/any_ref/schemas/crm_db/tables/customer_master/columns")
    assert columns.status_code == 200
    assert any(item["name"] == "id" for item in columns.json())

    files = client.get("/connections/any_ref/files")
    assert files.status_code == 200
    assert any(item["name"].endswith(".csv") for item in files.json())
