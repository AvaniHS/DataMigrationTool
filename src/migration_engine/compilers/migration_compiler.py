"""Orchestrates blueprint compilation into SQL fragments."""

from migration_engine.compilers.bootstrap.source_bootstrap_compiler import SourceBootstrapCompiler
from migration_engine.compilers.cte_naming import CteNaming
from migration_engine.compilers.cte_pipeline_builder import CtePipelineBuilder
from migration_engine.dialects.base_dialect import BaseDialect
from migration_engine.factories.conflict_strategy_factory import ConflictStrategyFactory
from migration_engine.models.blueprint import Blueprint
from migration_engine.models.connection import ConnectionConfig
from migration_engine.strategies.conflict.base import InsertContext


class MigrationCompiler:
    """Compiles a blueprint into bootstrap preamble, CTE pipeline, and target INSERT."""

    def __init__(self, dialect: BaseDialect) -> None:
        self._dialect = dialect
        self._pipeline_builder = CtePipelineBuilder()
        self._bootstrap_compiler = SourceBootstrapCompiler()

    def compile_blueprint(
        self,
        blueprint: Blueprint,
        connections: dict[str, ConnectionConfig],
    ) -> str:
        preamble = self._bootstrap_compiler.build(blueprint, connections)
        pipeline = self._pipeline_builder.build(blueprint, self._dialect)
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
        insert_sql = strategy.build_insert_statement(insert_context)

        sections = [section for section in (preamble, pipeline.render_with_clause(), insert_sql) if section]
        return "\n\n".join(sections) + ";"
