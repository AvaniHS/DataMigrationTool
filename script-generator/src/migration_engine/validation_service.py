"""Shared validation entry point for CLI and HTTP API."""

from __future__ import annotations

import json
from typing import Any

from migration_engine.models.enums import DialectType
from migration_engine.parsers.blueprint_parser import BlueprintParseError, BlueprintParser
from migration_engine.validators.migration_config_validator import MigrationConfigValidator
from migration_engine.validators.validation_result import ValidationReport


def validate_migration_payload(
    payload: dict[str, Any],
    *,
    dialect: DialectType = DialectType.MYSQL,
) -> dict[str, Any]:
    parser = BlueprintParser()
    migration_id = str(payload.get("migration_id", "unknown"))

    try:
        migration = parser.parse_text(json.dumps(payload))
    except BlueprintParseError as exc:
        report = ValidationReport(migration_id=migration_id, is_valid=True)
        if exc.details:
            for detail in exc.details:
                location = ".".join(str(part) for part in detail.get("loc", ()))
                report.add_issue(
                    code="PARSE_ERROR",
                    message=str(detail.get("msg", exc)),
                    path=location or "migration",
                )
        else:
            report.add_issue(
                code="PARSE_ERROR",
                message=str(exc),
                path="migration",
            )
        return report.to_dict()

    validator = MigrationConfigValidator(compile_dialect=dialect)
    report = validator.validate(migration)
    return report.to_dict()
