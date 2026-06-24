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


def test_copy_structure_mock_mode_creates_unprocessed_table(client: TestClient) -> None:
    response = client.post(
        "/connections/tgt_db/tables/copy-structure",
        json={
            "mode": "COPY_FROM_TABLE",
            "source_schema": "core",
            "source_table": "customers",
            "destination_schema": "core",
            "destination_table": "customers_unprocessed",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["created"] is True
    assert body["qualified_name"] == "core.customers_unprocessed"
    assert body["mode"] == "COPY_FROM_TABLE"


def test_copy_structure_audit_table_mock_mode(client: TestClient) -> None:
    response = client.post(
        "/connections/tgt_db/tables/copy-structure",
        json={
            "mode": "AUDIT_TABLE",
            "destination_schema": "core",
            "destination_table": "migration_conflict_mig_1",
            "migration_id": "mig_test_2026",
            "blueprint_sequence": 1,
            "target_schema": "core",
            "target_table": "customers",
            "primary_key_columns": ["id"],
            "target_columns": [
                {"name": "id", "data_type": "bigint", "is_nullable": False},
                {"name": "email", "data_type": "varchar", "is_nullable": True},
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["created"] is True
    assert body["mode"] == "AUDIT_TABLE"


def test_copy_structure_requires_source_for_copy_mode(client: TestClient) -> None:
    response = client.post(
        "/connections/tgt_db/tables/copy-structure",
        json={
            "mode": "COPY_FROM_TABLE",
            "destination_schema": "core",
            "destination_table": "customers_unprocessed",
        },
    )
    assert response.status_code == 422


def test_copy_structure_requires_audit_fields(client: TestClient) -> None:
    response = client.post(
        "/connections/tgt_db/tables/copy-structure",
        json={
            "mode": "AUDIT_TABLE",
            "destination_schema": "core",
            "destination_table": "migration_conflict_mig_1",
        },
    )
    assert response.status_code == 422
