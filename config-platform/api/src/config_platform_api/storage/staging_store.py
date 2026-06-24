"""Platform staging storage for uploaded CSV files."""

from __future__ import annotations

import re
import time
import uuid
from pathlib import Path

from config_platform_api.logging_setup import get_logger

logger = get_logger(__name__)

_STAGING_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


class StagingStore:
    def __init__(self, staging_dir: Path) -> None:
        self._staging_dir = staging_dir
        self._staging_dir.mkdir(parents=True, exist_ok=True)

    def connection_dir(self, connection_ref: str) -> Path:
        safe_ref = connection_ref.strip().lower()
        if not _STAGING_ID_PATTERN.match(safe_ref):
            raise ValueError("Invalid connection ref for staging storage.")
        path = self._staging_dir / safe_ref
        path.mkdir(parents=True, exist_ok=True)
        return path

    def staged_file_path(self, connection_ref: str, staging_file_id: str) -> Path:
        if not _STAGING_ID_PATTERN.match(staging_file_id):
            raise ValueError("Invalid staging file id.")
        return self.connection_dir(connection_ref) / f"{staging_file_id}.csv"

    def save_upload(self, connection_ref: str, content: bytes) -> str:
        staging_file_id = uuid.uuid4().hex
        target = self.staged_file_path(connection_ref, staging_file_id)
        target.write_bytes(content)
        logger.info(
            "staging_file_saved",
            connection_ref=connection_ref,
            staging_file_id=staging_file_id,
            bytes=len(content),
        )
        return staging_file_id

    def delete_connection_staging(self, connection_ref: str) -> None:
        directory = self._staging_dir / connection_ref.strip().lower()
        if not directory.exists():
            return
        for child in directory.glob("*.csv"):
            child.unlink(missing_ok=True)
        try:
            directory.rmdir()
        except OSError:
            pass
        logger.info("staging_connection_deleted", connection_ref=connection_ref)

    def purge_stale(self, *, ttl_days: int) -> int:
        if ttl_days <= 0:
            return 0
        cutoff = time.time() - (ttl_days * 86_400)
        removed = 0
        for csv_file in self._staging_dir.rglob("*.csv"):
            if csv_file.stat().st_mtime < cutoff:
                csv_file.unlink(missing_ok=True)
                removed += 1
        logger.info("staging_ttl_purge_complete", removed=removed, ttl_days=ttl_days)
        return removed
