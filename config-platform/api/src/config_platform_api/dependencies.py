from functools import lru_cache

from config_platform_api.config import get_settings
from config_platform_api.services.verification_store import VerificationStore
from config_platform_api.storage.connection_store import ConnectionStore
from config_platform_api.storage.migration_store import MigrationStore
from config_platform_api.storage.staging_store import StagingStore


@lru_cache
def get_connection_store() -> ConnectionStore:
    settings = get_settings()
    return ConnectionStore(settings.connections_file)


@lru_cache
def get_migration_store() -> MigrationStore:
    settings = get_settings()
    return MigrationStore(settings.migrations_file)


@lru_cache
def get_verification_store() -> VerificationStore:
    settings = get_settings()
    return VerificationStore(ttl_seconds=settings.verification_ttl_seconds)


@lru_cache
def get_staging_store() -> StagingStore:
    settings = get_settings()
    return StagingStore(settings.staging_dir)
