"""Connector adapter contract (§7.2.1)."""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

from sqlalchemy.engine import Engine

from config_platform_api.models.connectors import AuthMethodSchema, ConnectorMetadata


@dataclass(frozen=True)
class ConnectorTestResult:
    success: bool
    message: str


class ConnectorValidationError(ValueError):
    """Raised when connector_payload fails adapter validation."""


class BaseConnector(ABC):
    connector_id: ClassVar[str]
    label: ClassVar[str]
    description: ClassVar[str]
    category: ClassVar[str]
    export_type: ClassVar[str]

    @abstractmethod
    def auth_methods(self) -> list[AuthMethodSchema]:
        """Supported auth methods for catalog metadata."""

    def metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            connector_id=self.connector_id,
            label=self.label,
            description=self.description,
            category=self.category,  # type: ignore[arg-type]
            export_type=self.export_type,
            auth_methods=self.auth_methods(),
        )

    @abstractmethod
    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate and return normalized payload."""

    def fingerprint(self, payload: dict[str, Any]) -> str:
        validated = self.validate(payload)
        canonical = {
            "connector_id": self.connector_id,
            "payload": self._fingerprint_body(validated),
        }
        encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    @abstractmethod
    def _fingerprint_body(self, validated: dict[str, Any]) -> dict[str, Any]:
        """Canonical payload for fingerprinting (secrets included for save verification)."""

    @abstractmethod
    def test_connect(self, payload: dict[str, Any]) -> ConnectorTestResult:
        """Live connectivity probe from API host."""

    @abstractmethod
    def build_export(self, payload: dict[str, Any], *, secret_ref: str | None = None) -> dict[str, Any]:
        """Contract JSON fragment for migration export."""

    def create_engine(self, payload: dict[str, Any]) -> Engine:
        raise ConnectorValidationError(
            f"Connector '{self.connector_id}' does not support SQL introspection engines.",
        )

    @abstractmethod
    def build_summary(self, payload: dict[str, Any]) -> str:
        """Short summary for connection list UI."""

    def payload_schema_hint(self) -> dict[str, Any]:
        """Optional JSON-schema-like hint for GET /connectors/{id}/schema."""
        return {"auth_methods": [item.model_dump() for item in self.auth_methods()]}
