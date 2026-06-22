"""Shared SQL fragment builders for conflict strategies."""

from migration_engine.dialects.base_dialect import BaseDialect
from migration_engine.strategies.conflict.base import InsertContext


def format_column_list(columns: list[str]) -> str:
    return ", ".join(columns)


def build_select_from_projection(columns: list[str], projection_cte: str) -> str:
    column_list = format_column_list(columns)
    return f"SELECT {column_list}\nFROM {projection_cte}"


def build_insert_into(
    dialect: BaseDialect,
    ctx: InsertContext,
    *,
    ignore: bool = False,
    upsert: bool = False,
) -> str:
    table = dialect.qualify_table(ctx.target_schema, ctx.target_table)
    column_list = format_column_list(ctx.columns)
    insert_keyword = "INSERT IGNORE INTO" if ignore else "INSERT INTO"
    statement = (
        f"{insert_keyword} {table} ({column_list})\n"
        f"{build_select_from_projection(ctx.columns, ctx.projection_cte)}"
    )

    if upsert:
        statement = (
            f"{statement}\n"
            f"{dialect.on_duplicate_key_update(ctx.columns, ctx.primary_keys)}"
        )

    return statement


def build_preinsert_conflict_capture(
    dialect: BaseDialect,
    ctx: InsertContext,
    destination_table: str,
    *,
    rejected_at_column: str = "rejected_at",
) -> str:
    if not ctx.primary_keys:
        raise ValueError("Conflict capture requires at least one primary key column.")

    target = dialect.qualify_table(ctx.target_schema, ctx.target_table)
    destination = dialect.qualify_table(ctx.target_schema, destination_table)
    column_list = format_column_list(ctx.columns)
    projection_columns = ", ".join(f"p.{column}" for column in ctx.columns)
    join_predicate = dialect.primary_key_join("p", "t", ctx.primary_keys)

    return (
        f"INSERT INTO {destination} ({column_list}, {rejected_at_column})\n"
        f"SELECT {projection_columns}, NOW()\n"
        f"FROM {ctx.projection_cte} p\n"
        f"INNER JOIN {target} t ON {join_predicate}"
    )
