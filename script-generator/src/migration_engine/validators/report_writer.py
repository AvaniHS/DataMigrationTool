"""Validation report JSON export."""

from __future__ import annotations

import json
from pathlib import Path

from migration_engine.validators.validation_result import ValidationReport


def write_validation_report(report: ValidationReport, report_path: Path) -> Path:
    """Write a validation report as formatted JSON to disk."""
    resolved = report_path.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )
    return resolved
