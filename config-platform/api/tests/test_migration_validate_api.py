"""Tests for migration validation proxy."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from config_platform_api.dependencies import get_connection_store, get_migration_store, get_verification_store
from config_platform_api.main import app
from config_platform_api.models.connections import ConnectionSaveRequest
from config_platform_api.models.enums import OnConflictStrategy
from config_platform_api.models.migrations import (
    Blueprint,
    BlueprintSources,
    BlueprintTarget,
    ColumnMapping,
    CreateMigrationRequest,
    RootTableSource,
    UpdateMigrationRequest,
)
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


def _seed_valid_migration(
    connection_store: ConnectionStore,
    migration_store: MigrationStore,
) -> str:
    connection_store.create(
        ConnectionSaveRequest(
            ref="client_crm_mysql",
            connector_id="mysql",
            connector_payload={
                "auth_method": "password",
                "host": "client-crm-ip",
                "port": 3306,
                "database": "crm_db",
                "username": "read_user",
                "password": "pass",
                "use_advanced_string": False,
            },
            verification_token="verified",
        ),
        tested_at=datetime.now(UTC),
    )
    migration_store.create(
        CreateMigrationRequest(
            migration_id="mig_validate_api",
            client_id="client_acme",
            version="1.0.0",
            output_format="SQL",
        ),
    )
    migration_store.update(
        "mig_validate_api",
        UpdateMigrationRequest(
            client_id="client_acme",
            version="1.0.0",
            blueprints=[
                Blueprint(
                    sequence_order=1,
                    target=BlueprintTarget(
                        connection_ref="client_crm_mysql",
                        schema_name="core",
                        table_name="customers",
                        primary_keys=["id"],
                        on_conflict=OnConflictStrategy.UPSERT,
                    ),
                    sources=BlueprintSources(
                        root_table=RootTableSource(
                            connection_ref="client_crm_mysql",
                            alias="cm",
                            schema_name="crm_db",
                            table_name="customer_master",
                        ),
                        joins=[],
                    ),
                    mappings=[
                        ColumnMapping(
                            target_column="id",
                            source_type="DIRECT",
                            source_value="cm.id",
                            cast_to="INT",
                            is_nullable=False,
                        ),
                    ],
                ),
            ],
        ),
    )
    return "mig_validate_api"


def test_validate_migration_returns_issues_shape(client: TestClient) -> None:
    connection_store: ConnectionStore = app.dependency_overrides[get_connection_store]()
    migration_store: MigrationStore = app.dependency_overrides[get_migration_store]()
    migration_id = _seed_valid_migration(connection_store, migration_store)

    response = client.post(f"/migrations/{migration_id}/validate")
    assert response.status_code == 200
    payload = response.json()
    assert payload["migration_id"] == migration_id
    assert "is_valid" in payload
    assert "issues" in payload


def test_download_export_blocked_when_invalid(client: TestClient) -> None:
    migration_store: MigrationStore = app.dependency_overrides[get_migration_store]()
    migration_store.create(
        CreateMigrationRequest(
            migration_id="mig_invalid_download",
            client_id="client_acme",
            version="1.0.0",
            output_format="SQL",
        ),
    )
    migration_store.update(
        "mig_invalid_download",
        UpdateMigrationRequest(
            client_id="client_acme",
            version="1.0.0",
            blueprints=[
                Blueprint(
                    sequence_order=1,
                    target=BlueprintTarget(connection_ref="missing_ref"),
                    sources=BlueprintSources(),
                ),
            ],
        ),
    )

    response = client.get("/migrations/mig_invalid_download/export", params={"download": True})
    assert response.status_code == 422
