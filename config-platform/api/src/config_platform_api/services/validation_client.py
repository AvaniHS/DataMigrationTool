"""Validate migration exports via script-generator HTTP API or embedded monorepo engine."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
import structlog

from config_platform_api.config import Settings, get_settings

logger = structlog.get_logger(__name__)


class ValidationServiceError(RuntimeError):
    """Raised when validation cannot be executed."""


def validate_migration_export(
    export_payload: dict[str, Any],
    *,
    settings: Settings | None = None,
) -> dict[str, Any]:
    active_settings = settings or get_settings()
    if active_settings.script_generator_url:
        return _validate_via_http(active_settings, export_payload)
    return _validate_embedded(export_payload)


def _validate_via_http(settings: Settings, export_payload: dict[str, Any]) -> dict[str, Any]:
    base_url = settings.script_generator_url.rstrip("/") + "/"
    url = urljoin(base_url, "validate")
    try:
        with httpx.Client(timeout=settings.validation_timeout_seconds) as client:
            response = client.post(url, json=export_payload)
    except httpx.RequestError as exc:
        logger.error(
            "script_generator_unreachable",
            url=url,
            error=str(exc),
            exc_info=True,
        )
        raise ValidationServiceError(
            "Unable to reach the script generator validation service. "
            "Start it or configure embedded validation for local development.",
        ) from exc

    if response.status_code >= 500:
        logger.error(
            "script_generator_validation_failed",
            url=url,
            status_code=response.status_code,
            body=response.text,
        )
        raise ValidationServiceError("Script generator validation service returned an error.")

    try:
        return response.json()
    except ValueError as exc:
        raise ValidationServiceError("Script generator returned invalid validation JSON.") from exc


def _validate_embedded(export_payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_script_generator_import_path()
    try:
        from migration_engine.validation_service import validate_migration_payload
    except ImportError as exc:
        logger.error("embedded_validator_import_failed", error=str(exc), exc_info=True)
        raise ValidationServiceError(
            "Embedded validator is unavailable. Set CONFIG_API_SCRIPT_GENERATOR_URL "
            "or install the migration-engine package from script-generator/.",
        ) from exc

    return validate_migration_payload(export_payload)


def _ensure_script_generator_import_path() -> None:
    script_generator_src = _script_generator_src_path()
    src_text = str(script_generator_src)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)


def _script_generator_src_path() -> Path:
    repo_root = Path(__file__).resolve().parents[5]
    return repo_root / "script-generator" / "src"


def to_validation_report_response(report_dict: dict[str, Any]) -> dict[str, Any]:
    return {
        "migration_id": str(report_dict.get("migration_id", "unknown")),
        "is_valid": bool(report_dict.get("is_valid", False)),
        "issue_count": int(report_dict.get("issue_count", len(report_dict.get("issues", [])))),
        "issues": [
            {
                "code": str(issue.get("code", "VALIDATION_ERROR")),
                "message": str(issue.get("message", "")),
                "path": str(issue.get("path", "")),
                "blueprint_sequence": issue.get("blueprint_sequence"),
            }
            for issue in report_dict.get("issues", [])
        ],
    }
