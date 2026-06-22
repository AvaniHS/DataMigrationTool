"""Factory for script generators."""

from migration_engine.generators.base_script_generator import IScriptGenerator
from migration_engine.generators.sql_script_generator import SqlScriptGenerator
from migration_engine.models.enums import OutputFormat


class ScriptGeneratorFactory:
    """Creates script generators by output format."""

    _registry: dict[str, type[IScriptGenerator]] = {
        OutputFormat.SQL.value: SqlScriptGenerator,
    }

    @classmethod
    def create(cls, output_format: str) -> IScriptGenerator:
        generator_cls = cls._registry.get(output_format.upper())
        if generator_cls is None:
            supported = ", ".join(sorted(cls._registry))
            raise ValueError(
                f"Unsupported output format '{output_format}'. Supported: {supported}"
            )
        return generator_cls()

    @classmethod
    def register(cls, output_format: str, generator_cls: type[IScriptGenerator]) -> None:
        cls._registry[output_format.upper()] = generator_cls
