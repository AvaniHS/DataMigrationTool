"""Orchestrates all migration config validators."""

from pathlib import Path

from migration_engine.models import MasterMigrationBlueprint
from migration_engine.models.enums import DialectType
from migration_engine.validators.connectivity_validator import ConnectivityValidator
from migration_engine.validators.expression_validator import ExpressionValidator
from migration_engine.validators.schema_validator import SchemaValidator
from migration_engine.validators.validation_result import ValidationReport


class MigrationConfigValidator:
    """Runs schema, expression, and connectivity validators in sequence."""

    def __init__(
        self,
        compile_dialect: DialectType = DialectType.MYSQL,
        whitelist_path: Path | None = None,
    ) -> None:
        self._schema_validator = SchemaValidator()
        self._expression_validator = ExpressionValidator(whitelist_path)
        self._connectivity_validator = ConnectivityValidator(compile_dialect)

    def validate(self, blueprint: MasterMigrationBlueprint) -> ValidationReport:
        report = ValidationReport(migration_id=blueprint.migration_id, is_valid=True)
        report.merge(self._schema_validator.validate(blueprint))
        report.merge(self._expression_validator.validate(blueprint))
        report.merge(self._connectivity_validator.validate(blueprint))
        return report
