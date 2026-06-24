"""Filesystem path allowlisting for local CSV connections."""

from __future__ import annotations

from pathlib import Path

from config_platform_api.connectors.base import ConnectorValidationError


def resolve_allowed_path(file_path: str, allowed_roots: list[Path]) -> Path:
    candidate = Path(file_path).expanduser()
    try:
        resolved = candidate.resolve(strict=False)
    except OSError as exc:
        raise ConnectorValidationError(f"Invalid file path: {exc}") from exc

    if ".." in Path(file_path).parts:
        raise ConnectorValidationError("Path traversal is not allowed.")

    if not allowed_roots:
        raise ConnectorValidationError(
            "No file roots are configured on the API host. Set CONFIG_API_FILE_ROOTS."
        )

    for root in allowed_roots:
        root_resolved = root.expanduser().resolve(strict=False)
        try:
            resolved.relative_to(root_resolved)
            return resolved
        except ValueError:
            continue

    raise ConnectorValidationError(
        "File path is outside allowed roots. "
        f"Allowed: {', '.join(str(root) for root in allowed_roots)}. "
        "Add a parent directory via CONFIG_API_FILE_ROOTS on the API host, "
        "or use Platform upload instead."
    )
