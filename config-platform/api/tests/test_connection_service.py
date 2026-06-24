from pathlib import Path

import pytest
from fastapi import HTTPException

from config_platform_api.models.connections import ConnectionSaveRequest
from config_platform_api.services.connection_service import save_verified_connection
from config_platform_api.services.verification_store import VerificationStore
from config_platform_api.storage.connection_store import ConnectionStore


def _save_request(ref: str = "demo_mysql", verification_token: str = "token") -> ConnectionSaveRequest:
    return ConnectionSaveRequest(
        ref=ref,
        connector_id="mysql",
        connector_payload={
            "auth_method": "password",
            "host": "localhost",
            "port": 3306,
            "database": "crm_db",
            "username": "read_user",
            "password": "pass",
            "use_advanced_string": False,
        },
        verification_token=verification_token,
    )


def test_save_requires_verification_token(tmp_path: Path) -> None:
    store = ConnectionStore(tmp_path / "connections.json")
    verification = VerificationStore(ttl_seconds=900)

    with pytest.raises(HTTPException) as exc_info:
        save_verified_connection(_save_request(), store, verification, is_create=True)

    assert exc_info.value.status_code == 400
