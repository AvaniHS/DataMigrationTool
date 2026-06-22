"""Builds the CTE pipeline for a single blueprint."""

from migration_engine.compilers.cte_models import CtePipeline, CteStage
from migration_engine.compilers.cte_naming import CteNaming
from migration_engine.compilers.join_clause_builder import (
    render_join_from_clause,
    render_star_select_for_aliases,
)
from migration_engine.compilers.mapping_resolver import resolve_mapping_expression
from migration_engine.dialects.base_dialect import BaseDialect
from migration_engine.models.blueprint import Blueprint


class CtePipelineBuilder:
    """Constructs deterministic CTE stages from a blueprint definition."""

    def build(self, blueprint: Blueprint, dialect: BaseDialect) -> CtePipeline:
        naming = CteNaming(blueprint.sequence_order)
        root_alias = blueprint.sources.root_table.alias
        stages: list[CteStage] = []

        stages.extend(self._build_source_stages(blueprint, naming))
        stages.append(self._build_pre_filter_stage(blueprint, naming, root_alias))
        stages.append(self._build_join_stage(blueprint, naming, root_alias))
        stages.append(self._build_derivation_stage(blueprint, naming, root_alias))
        projection_source = self._append_post_filter_stage(stages, blueprint, naming)
        stages.append(
            self._build_projection_stage(
                blueprint,
                dialect,
                naming,
                projection_source,
            )
        )

        return CtePipeline(
            stages=tuple(stages),
            projection_cte=naming.target_projection(),
        )

    def _build_source_stages(
        self, blueprint: Blueprint, naming: CteNaming
    ) -> list[CteStage]:
        aliases = self._collect_source_aliases(blueprint)
        stages: list[CteStage] = []

        for alias in aliases:
            source = self._find_source_by_alias(blueprint, alias)
            comment = source.comment or ""
            body = (
                f"SELECT *\nFROM {naming.bootstrap_table(alias)}"
            )
            stages.append(CteStage(name=naming.stg(alias), body=body, comment=comment))

        return stages

    def _build_pre_filter_stage(
        self, blueprint: Blueprint, naming: CteNaming, root_alias: str
    ) -> CteStage:
        source_cte = naming.stg(root_alias)
        if blueprint.pre_filters:
            predicates = " AND ".join(blueprint.pre_filters)
            body = (
                f"SELECT *\nFROM {source_cte} AS {root_alias}\n"
                f"WHERE {predicates}"
            )
        else:
            body = f"SELECT *\nFROM {source_cte} AS {root_alias}"

        return CteStage(
            name=naming.pre_filtered(root_alias),
            body=body,
        )

    def _build_join_stage(
        self, blueprint: Blueprint, naming: CteNaming, root_alias: str
    ) -> CteStage:
        joins = blueprint.sources.joins
        pre_filtered_cte = naming.pre_filtered(root_alias)

        if not joins:
            body = f"SELECT *\nFROM {pre_filtered_cte} AS {root_alias}"
        else:
            aliases = [root_alias, *(join.alias for join in joins)]
            select_list = render_star_select_for_aliases(aliases)
            from_clause = render_join_from_clause(
                root_alias=root_alias,
                pre_filtered_cte=pre_filtered_cte,
                joins=joins,
                staging_cte_name=naming.stg,
            )
            body = f"SELECT {select_list}\n{from_clause}"

        return CteStage(name=naming.joined(root_alias), body=body)

    def _build_derivation_stage(
        self, blueprint: Blueprint, naming: CteNaming, root_alias: str
    ) -> CteStage:
        joins = blueprint.sources.joins
        pre_filtered_cte = naming.pre_filtered(root_alias)

        if joins:
            aliases = [root_alias, *(join.alias for join in joins)]
            select_prefix = render_star_select_for_aliases(aliases)
            from_clause = render_join_from_clause(
                root_alias=root_alias,
                pre_filtered_cte=pre_filtered_cte,
                joins=joins,
                staging_cte_name=naming.stg,
            )
            select_lines = [select_prefix]
            from_lines = [from_clause]
        else:
            select_lines = [f"{root_alias}.*"]
            from_lines = [f"FROM {pre_filtered_cte} AS {root_alias}"]

        for derivation in blueprint.derivations:
            select_lines.append(f"{derivation.expression} AS {derivation.variable_name}")

        body = f"SELECT {', '.join(select_lines)}\n" + "\n".join(from_lines)

        return CteStage(name=naming.calculation_layer(), body=body)

    def _append_post_filter_stage(
        self,
        stages: list[CteStage],
        blueprint: Blueprint,
        naming: CteNaming,
    ) -> str:
        if not blueprint.post_filters:
            return naming.calculation_layer()

        predicates = " AND ".join(blueprint.post_filters)
        body = (
            f"SELECT *\nFROM {naming.calculation_layer()}\n"
            f"WHERE {predicates}"
        )
        stages.append(CteStage(name=naming.filtered_results(), body=body))
        return naming.filtered_results()

    def _build_projection_stage(
        self,
        blueprint: Blueprint,
        dialect: BaseDialect,
        naming: CteNaming,
        source_cte: str,
    ) -> CteStage:
        projection_columns: list[str] = []
        for mapping in blueprint.mappings:
            expression = resolve_mapping_expression(mapping)
            cast_expression = dialect.safe_cast(expression, mapping.cast_to)
            projection_columns.append(f"{cast_expression} AS {mapping.target_column}")

        column_sql = ",\n    ".join(projection_columns)
        body = f"SELECT\n    {column_sql}\nFROM {source_cte}"

        return CteStage(name=naming.target_projection(), body=body)

    def _collect_source_aliases(self, blueprint: Blueprint) -> list[str]:
        aliases = [blueprint.sources.root_table.alias]
        aliases.extend(join.alias for join in blueprint.sources.joins)
        return aliases

    def _find_source_by_alias(self, blueprint: Blueprint, alias: str):
        if blueprint.sources.root_table.alias == alias:
            return blueprint.sources.root_table
        for join in blueprint.sources.joins:
            if join.alias == alias:
                return join
        raise ValueError(f"Unknown source alias '{alias}'.")
