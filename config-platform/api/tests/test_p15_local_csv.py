from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from config_platform_api.config import Settings, get_settings
from config_platform_api.dependencies import get_connection_store, get_staging_store, get_verification_store
from config_platform_api.main import app
from config_platform_api.services.verification_store import VerificationStore
from config_platform_api.storage.connection_store import ConnectionStore
from config_platform_api.storage.staging_store import StagingStore


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    root = tmp_path / "data"
    root.mkdir()
    sample = root / "customers.csv"
    sample.write_text("id,name\n1,Alice\n", encoding="utf-8")
    return root


@pytest.fixture
def client(data_root: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    staging_dir = data_root / "staging"
    settings = Settings(
        connections_file=data_root / "connections.json",
        migrations_file=data_root / "migrations.json",
        staging_dir=staging_dir,
        file_roots=[str(data_root)],
        max_upload_mb=1,
        staging_ttl_days=30,
    )
    monkeypatch.setattr("config_platform_api.config.get_settings", lambda: settings)

    store = ConnectionStore(settings.connections_file)
    verification = VerificationStore(ttl_seconds=900)
    staging_store = StagingStore(staging_dir)

    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_connection_store] = lambda: store
    app.dependency_overrides[get_verification_store] = lambda: verification
    app.dependency_overrides[get_staging_store] = lambda: staging_store

    yield TestClient(app)
    app.dependency_overrides.clear()


def _local_path_payload(file_path: str) -> dict[str, object]:
    return {
        "location_kind": "local_path",
        "file_path": file_path,
        "staging_file_id": "",
        "parse_options": {
            "delimiter": ",",
            "quote": '"',
            "header_row": 1,
            "encoding": "utf-8",
        },
    }


def test_local_csv_path_test_succeeds(client: TestClient, data_root: Path) -> None:
    response = client.post(
        "/connections/test",
        json={
            "connector_id": "local_csv",
            "connector_payload": _local_path_payload(str(data_root / "customers.csv")),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "2 column" in body["message"]
    assert body["verification_token"]


def test_local_csv_rejects_path_outside_roots(client: TestClient) -> None:
    response = client.post(
        "/connections/test",
        json={
            "connector_id": "local_csv",
            "connector_payload": _local_path_payload("C:\\outside\\secret.csv"),
        },
    )
    assert response.status_code == 200
    assert response.json()["success"] is False


def test_local_csv_upload_and_test(client: TestClient, data_root: Path) -> None:
    upload = client.post(
        "/connections/sample_csv/files/upload",
        files={"file": ("orders.csv", b"order_id,amount\n1,9.99\n", "text/csv")},
    )
    assert upload.status_code == 201
    staging_file_id = upload.json()["staging_file_id"]

    test_response = client.post(
        "/connections/test",
        json={
            "connector_id": "local_csv",
            "connection_ref": "sample_csv",
            "connector_payload": {
                "location_kind": "platform_staging",
                "file_path": "",
                "staging_file_id": staging_file_id,
                "parse_options": _local_path_payload("")["parse_options"],
            },
        },
    )
    assert test_response.status_code == 200
    assert test_response.json()["success"] is True

    token = test_response.json()["verification_token"]
    save_response = client.post(
        "/connections",
        json={
            "ref": "sample_csv",
            "connector_id": "local_csv",
            "connector_payload": {
                "location_kind": "platform_staging",
                "file_path": "",
                "staging_file_id": staging_file_id,
                "parse_options": _local_path_payload("")["parse_options"],
            },
            "verification_token": token,
        },
    )
    assert save_response.status_code == 201

    files_response = client.get("/connections/sample_csv/files")
    assert files_response.status_code == 200
    file_name = files_response.json()[0]["name"]

    columns_response = client.get(f"/connections/sample_csv/files/{file_name}/columns")
    assert columns_response.status_code == 200
    assert [item["name"] for item in columns_response.json()] == ["order_id", "amount"]

    export_response = client.get("/connections/export")
    exported = export_response.json()["sample_csv"]
    assert exported["type"] == "LOCAL_CSV"
    assert exported["staging_file_id"] == staging_file_id
    assert "connection_string" not in exported


def test_upload_rejects_oversized_file(client: TestClient) -> None:
    oversized = b"x" * (1_048_576 + 1)
    response = client.post(
        "/connections/big/files/upload",
        files={"file": ("big.csv", oversized, "text/csv")},
    )
    assert response.status_code == 413
