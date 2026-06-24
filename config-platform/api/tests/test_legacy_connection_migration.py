import json
from pathlib import Path

from config_platform_api.storage.connection_store import ConnectionStore


def test_connection_store_migrates_legacy_records_on_read(tmp_path: Path) -> None:
    storage_path = tmp_path / "connections.json"
    storage_path.write_text(
        json.dumps(
            {
                "client_crm_mysql": {
                    "ref": "client_crm_mysql",
                    "type": "MYSQL",
                    "secret_ref": None,
                    "database": {
                        "host": "client-crm-ip",
                        "port": 3306,
                        "database": "crm_db",
                        "username": "read_user",
                        "password": "pass",
                        "use_advanced_string": False,
                    },
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                    "last_tested_at": None,
                },
            },
        ),
        encoding="utf-8",
    )

    store = ConnectionStore(storage_path)
    record = store.get("client_crm_mysql")
    assert record.connector_id == "mysql"
    assert record.connector_payload["host"] == "client-crm-ip"
