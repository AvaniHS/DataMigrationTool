"""Collects blueprint sources and builds bootstrap preambles."""

from migration_engine.compilers.bootstrap.bootstrap_strategy_factory import BootstrapStrategyFactory
from migration_engine.compilers.bootstrap.context import SourceBootstrapContext, SourceBootstrapRequest
from migration_engine.compilers.cte_naming import CteNaming
from migration_engine.models.blueprint import Blueprint, FileJoin, FileSource, JoinSource, RootSource
from migration_engine.models.connection import ConnectionConfig
from migration_engine.models.enums import ConnectionType


class SourceBootstrapCompiler:
    """Generates SQL preamble statements for all sources in a blueprint."""

    def build(
        self,
        blueprint: Blueprint,
        connections: dict[str, ConnectionConfig],
    ) -> str:
        blocks: list[str] = []
        naming = CteNaming(blueprint.sequence_order)

        for source in self._collect_sources(blueprint):
            connection = connections.get(source.connection_ref)
            if connection is None:
                raise ValueError(
                    f"Unknown connection reference '{source.connection_ref}' "
                    f"for source alias '{source.alias}'."
                )

            context = SourceBootstrapContext(
                alias=source.alias,
                connection_ref=source.connection_ref,
                connection_type=ConnectionType(connection.type),
                bootstrap_table=naming.bootstrap_table(source.alias),
                schema_name=getattr(source, "schema", None),
                table_name=getattr(source, "table_name", None),
                file_name=getattr(source, "file_name", None),
                comment=source.comment,
            )
            strategy = BootstrapStrategyFactory.create(connection.type.value)
            request = SourceBootstrapRequest(source=context, connection=connection)
            preamble = strategy.build_preamble(request)
            if context.comment:
                preamble = f"-- {context.comment}\n{preamble}"
            blocks.append(preamble)

        return "\n\n".join(blocks)

    def _collect_sources(self, blueprint: Blueprint) -> list[RootSource | JoinSource]:
        sources: list[RootSource | JoinSource] = [blueprint.sources.root_table]
        sources.extend(blueprint.sources.joins)
        return sources
