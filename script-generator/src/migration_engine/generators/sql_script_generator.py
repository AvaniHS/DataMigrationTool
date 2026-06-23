"""SQL script generator."""

from migration_engine.compilers.migration_compiler import MigrationCompiler
from migration_engine.factories.dialect_factory import DialectFactory
from migration_engine.generators.base_script_generator import GeneratedScript, IScriptGenerator
from migration_engine.generators.errors import ScriptGenerationError
from migration_engine.models import MasterMigrationBlueprint
from migration_engine.models.enums import DialectType, OutputFormat
from migration_engine.validators.migration_config_validator import MigrationConfigValidator


class SqlScriptGenerator(IScriptGenerator):
    """Compiles validated blueprints into runnable SQL scripts."""

    def __init__(self, dialect_type: str = DialectType.MYSQL.value) -> None:
        self._dialect_type = dialect_type

    def generate(self, blueprint: MasterMigrationBlueprint) -> GeneratedScript:
        dialect_enum = self._resolve_dialect(self._dialect_type)
        self._validate_or_raise(blueprint, dialect_enum)

        dialect = DialectFactory.create(dialect_enum.value)
        compiler = MigrationCompiler(dialect)
        content = compiler.compile_migration(blueprint)

        return GeneratedScript(
            content=content,
            migration_id=blueprint.migration_id,
            output_format=OutputFormat.SQL.value,
        )

    def _validate_or_raise(
        self,
        blueprint: MasterMigrationBlueprint,
        dialect_enum: DialectType,
    ) -> None:
        report = MigrationConfigValidator(compile_dialect=dialect_enum).validate(blueprint)
        if report.is_valid:
            return

        raise ScriptGenerationError(
            report.format_summary(),
            validation_report=report,
        )

    def _resolve_dialect(self, dialect_type: str) -> DialectType:
        try:
            return DialectType(dialect_type.upper())
        except ValueError as exc:
            raise ScriptGenerationError(f"Unsupported dialect: {dialect_type}") from exc
