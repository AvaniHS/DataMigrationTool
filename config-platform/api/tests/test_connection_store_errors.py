import json
from pathlib import Path

import pytest

from config_platform_api.exceptions import ConnectionStoreError
from config_platform_api.storage.connection_store import ConnectionStore


def test_read_corrupt_registry_raises_store_error(tmp_path: Path) -> None:
    storage_path = tmp_path / "connections.json"
    storage_path.write_text("{bad", encoding="utf-8")
    store = ConnectionStore(storage_path)

    with pytest.raises(ConnectionStoreError, match="unavailable"):
        store.list_items()


def test_write_failure_raises_store_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    storage_path = tmp_path / "connections.json"
    store = ConnectionStore(storage_path)

    def fail_write(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", fail_write)

    payload = {
        "ref": "demo",
        "connector_id": "mysql",
        "connector_payload": {
            "auth_method": "password",
            "host": "localhost",
            "port": 3306,
            "database": "db",
            "username": "user",
            "password": "",
            "use_advanced_string": False,
        },
        "verification_token": "token",
    }
    from config_platform_api.models.connections import ConnectionSaveRequest

    request = ConnectionSaveRequest.model_validate(payload)
    from datetime import UTC, datetime

    with pytest.raises(ConnectionStoreError, match="unavailable"):
        store.create(request, tested_at=datetime.now(UTC))
