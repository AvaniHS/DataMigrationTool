"""Persistence contracts for dependency injection."""

from datetime import datetime
from typing import Protocol

from config_platform_api.models.connections import ConnectionListItem, ConnectionRecord, ConnectionSaveRequest


class ConnectionStoreProtocol(Protocol):
    def list_items(self) -> list[ConnectionListItem]: ...

    def get(self, ref: str) -> ConnectionRecord: ...

    def create(self, request: ConnectionSaveRequest, *, tested_at: datetime) -> ConnectionRecord: ...

    def update(self, ref: str, request: ConnectionSaveRequest, *, tested_at: datetime) -> ConnectionRecord: ...

    def delete(self, ref: str) -> None: ...

    def export_all(self) -> dict[str, dict[str, str]]: ...
