"""Orchestrates blueprint and migration compilation into SQL scripts."""

from migration_engine.compilers.bootstrap.source_bootstrap_compiler import SourceBootstrapCompiler
from migration_engine.compilers.chunking_procedural_builder import ChunkingProceduralBuilder
from migration_engine.compilers.cte_naming import CteNaming
from migration_engine.compilers.cte_pipeline_builder import CtePipelineBuilder
from migration_engine.compilers.transaction_builder import TransactionBuilder
from migration_engine.dialects.base_dialect import BaseDialect
from migration_engine.factories.conflict_strategy_factory import ConflictStrategyFactory
from migration_engine.models.blueprint import Blueprint, MasterMigrationBlueprint
from migration_engine.models.connection import ConnectionConfig
from migration_engine.strategies.conflict.base import InsertContext


class MigrationCompiler:
    """Compiles blueprints and full migrations into runnable SQL scripts."""

    def __init__(self, dialect: BaseDialect) -> None:
        self._dialect = dialect
        self._pipeline_builder = CtePipelineBuilder()
        self._bootstrap_compiler = SourceBootstrapCompiler()
        self._transaction_builder = TransactionBuilder(dialect)
        self._chunking_builder = ChunkingProceduralBuilder(dialect)

    def compile_migration(self, migration: MasterMigrationBlueprint) -> str:
        """Compile all blueprints into a single ordered SQL script."""
        ordered_blueprints = sorted(
            migration.blueprints,
            key=lambda blueprint: blueprint.sequence_order,
        )
        blocks = [
            self.compile_blueprint(blueprint, migration.connections)
            for blueprint in ordered_blueprints
        ]
        header = self._build_script_header(migration)
        return "\n\n".join([header, *blocks])

    def compile_blueprint(
        self,
        blueprint: Blueprint,
        connections: dict[str, ConnectionConfig],
    ) -> str:
        """Compile one blueprint with bootstrap, optional chunking, and transaction boundaries."""
        body = self._compile_blueprint_body(blueprint, connections)
        return self._transaction_builder.wrap_blueprint_block(blueprint.sequence_order, body)

    def _compile_blueprint_body(
        self,
        blueprint: Blueprint,
        connections: dict[str, ConnectionConfig],
    ) -> str:
        preamble = self._bootstrap_compiler.build(blueprint, connections)
        use_chunking = blueprint.chunking_strategy.is_enabled
        pipeline = self._pipeline_builder.build(
            blueprint,
            self._dialect,
            use_chunk_filter=use_chunking,
        )
        insert_sql = self._build_insert_statement(blueprint)
        load_sql = f"{pipeline.render_with_clause()}\n{insert_sql}"

        sections: list[str] = []
        if preamble:
            sections.append(preamble)
        if use_chunking:
            sections.append(self._chunking_builder.build_setup_statements(blueprint))
            sections.append(self._chunking_builder.wrap_in_chunk_loop(blueprint, load_sql))
        else:
            sections.append(f"{load_sql};")

        return "\n\n".join(section for section in sections if section)

    def _build_insert_statement(self, blueprint: Blueprint) -> str:
        naming = CteNaming(blueprint.sequence_order)
        target = blueprint.target
        columns = [mapping.target_column for mapping in blueprint.mappings]

        insert_context = InsertContext(
            target_schema=target.schema,
            target_table=target.table_name,
            columns=columns,
            projection_cte=naming.target_projection(),
            primary_keys=target.primary_keys,
            unprocessed_table=target.unprocessed_table,
        )
        strategy = ConflictStrategyFactory.create(target.on_conflict.value, self._dialect)
        return strategy.build_insert_statement(insert_context)

    def _build_script_header(self, migration: MasterMigrationBlueprint) -> str:
        return "\n".join(
            [
                "-- ============================================================",
                f"-- Migration: {migration.migration_id}",
                f"-- Client: {migration.client_id}",
                f"-- Version: {migration.version}",
                "-- ============================================================",
            ]
        )
