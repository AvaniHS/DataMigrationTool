"""Shared SQL builders for join clauses."""

from collections.abc import Callable

from migration_engine.models.blueprint import JoinSource
from migration_engine.models.mapping import JoinCondition


def format_join_condition(condition: JoinCondition) -> str:
    return f"{condition.left_expression} {condition.operator} {condition.right_expression}"


def format_join_conditions(conditions: list[JoinCondition]) -> str:
    return " AND ".join(format_join_condition(condition) for condition in conditions)


def render_star_select_for_aliases(aliases: list[str]) -> str:
    return ", ".join(f"{alias}.*" for alias in aliases)


def render_join_from_clause(
    root_alias: str,
    pre_filtered_cte: str,
    joins: list[JoinSource],
    staging_cte_name: Callable[[str], str],
) -> str:
    """Render FROM pre_filtered root plus configured joins with original aliases."""
    lines = [f"FROM {pre_filtered_cte} AS {root_alias}"]
    for join in joins:
        join_keyword = join.join_type.value
        join_cte = staging_cte_name(join.alias)
        predicate = format_join_conditions(join.conditions)
        lines.append(
            f"{join_keyword} JOIN {join_cte} AS {join.alias}\n  ON {predicate}"
        )
    return "\n".join(lines)
