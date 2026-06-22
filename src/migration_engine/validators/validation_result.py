"""Validation result models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation failure."""

    code: str
    message: str
    path: str = ""
    blueprint_sequence: int | None = None


@dataclass
class ValidationReport:
    """Aggregated validation outcome."""

    migration_id: str
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    def add_issue(
        self,
        code: str,
        message: str,
        path: str = "",
        blueprint_sequence: int | None = None,
    ) -> None:
        self.issues.append(
            ValidationIssue(
                code=code,
                message=message,
                path=path,
                blueprint_sequence=blueprint_sequence,
            )
        )
        self.is_valid = False

    def merge(self, other: ValidationReport) -> None:
        """Combine issues from another validation report."""
        if not other.is_valid:
            self.is_valid = False
        self.issues.extend(other.issues)

    def to_dict(self) -> dict:
        return {
            "migration_id": self.migration_id,
            "is_valid": self.is_valid,
            "issue_count": len(self.issues),
            "issues": [
                {
                    "code": issue.code,
                    "message": issue.message,
                    "path": issue.path,
                    "blueprint_sequence": issue.blueprint_sequence,
                }
                for issue in self.issues
            ],
        }

    def format_summary(self) -> str:
        """Return a concise human-readable summary for CLI output."""
        if self.is_valid:
            return f"Validation passed for migration '{self.migration_id}'."

        lines = [
            f"Validation failed for migration '{self.migration_id}' "
            f"with {len(self.issues)} issue(s):",
        ]
        for index, issue in enumerate(self.issues, start=1):
            location = issue.path or "migration"
            if issue.blueprint_sequence is not None:
                location = f"{location} (blueprint {issue.blueprint_sequence})"
            lines.append(f"  {index}. [{issue.code}] {location}: {issue.message}")
        return "\n".join(lines)
