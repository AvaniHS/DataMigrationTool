"""SQL script generation errors."""

from migration_engine.validators.validation_result import ValidationReport


class ScriptGenerationError(Exception):
    """Raised when SQL script generation cannot complete."""

    def __init__(
        self,
        message: str,
        *,
        validation_report: ValidationReport | None = None,
    ) -> None:
        super().__init__(message)
        self.validation_report = validation_report
