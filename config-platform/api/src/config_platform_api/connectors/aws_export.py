"""AWS export block helpers (non-secrets only)."""

from __future__ import annotations

from typing import Any


def build_aws_export_block(validated: dict[str, Any]) -> dict[str, str] | None:
    region = str(validated.get("aws_region", "")).strip()
    if not region:
        return None
    return {"region": region}
