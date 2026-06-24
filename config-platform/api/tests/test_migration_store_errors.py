from pathlib import Path

import pytest

from config_platform_api.exceptions import MigrationStoreError
from config_platform_api.storage.migration_store import MigrationStore


def test_migration_store_read_failure(tmp_path: Path) -> None:
    storage_path = tmp_path / "migrations.json"
    storage_path.write_text("{not-json", encoding="utf-8")
    store = MigrationStore(storage_path)

    with pytest.raises(MigrationStoreError):
        store.list_items()
