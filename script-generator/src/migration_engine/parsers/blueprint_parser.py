"""Parses migration JSON files into immutable DTOs."""

import json
from pathlib import Path

from pydantic import ValidationError

from migration_engine.models import MasterMigrationBlueprint


class BlueprintParseError(Exception):
    """Raised when JSON cannot be parsed into a blueprint DTO."""

    def __init__(self, message: str, details: list[dict] | None = None) -> None:
        super().__init__(message)
        self.details = details or []


class BlueprintParser:
    """Reads JSON configuration files and returns frozen blueprint DTOs."""

    def parse_file(self, config_path: Path) -> MasterMigrationBlueprint:
        """Load and parse a migration JSON file from disk."""
        if not config_path.is_file():
            raise BlueprintParseError(f"Config file not found: {config_path}")

        raw_text = config_path.read_text(encoding="utf-8")
        return self.parse_text(raw_text)

    def parse_text(self, raw_text: str) -> MasterMigrationBlueprint:
        """Parse migration JSON text into a blueprint DTO."""
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise BlueprintParseError(f"Invalid JSON: {exc}") from exc

        if not isinstance(payload, dict):
            raise BlueprintParseError("Migration config root must be a JSON object.")

        payload = self._strip_json_schema_metadata(payload)
        return self._to_dto(payload)

    def _strip_json_schema_metadata(self, payload: dict) -> dict:
        """Remove JSON Schema metadata keys that are not part of the DTO."""
        return {key: value for key, value in payload.items() if key != "$schema"}

    def _to_dto(self, payload: dict) -> MasterMigrationBlueprint:
        try:
            return MasterMigrationBlueprint.model_validate(payload)
        except ValidationError as exc:
            details = exc.errors()
            message = "; ".join(
                f"{'.'.join(str(part) for part in err.get('loc', ()))}: {err.get('msg')}"
                for err in details
            )
            raise BlueprintParseError(f"Blueprint schema validation failed: {message}", details) from exc
