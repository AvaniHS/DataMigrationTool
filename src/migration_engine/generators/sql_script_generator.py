"""SQL script generator — implemented in Phase 6."""

from migration_engine.generators.base_script_generator import GeneratedScript, IScriptGenerator
from migration_engine.models import MasterMigrationBlueprint


class SqlScriptGenerator(IScriptGenerator):
    """Compiles blueprints into runnable SQL scripts."""

    def generate(self, blueprint: MasterMigrationBlueprint) -> GeneratedScript:
        raise NotImplementedError("SQL generation is implemented in Phase 6.")
