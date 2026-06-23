from functools import lru_cache
from pathlib import Path

from config_platform_api.config import get_settings
from config_platform_api.services.verification_store import VerificationStore
from config_platform_api.storage.connection_store import ConnectionStore


@lru_cache
def get_connection_store() -> ConnectionStore:
    settings = get_settings()
    return ConnectionStore(settings.connections_file)


@lru_cache
def get_verification_store() -> VerificationStore:
    settings = get_settings()
    return VerificationStore(ttl_seconds=settings.verification_ttl_seconds)
