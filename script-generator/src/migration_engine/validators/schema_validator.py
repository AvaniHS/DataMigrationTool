"""Structural and business-rule validation for migration blueprints."""

from migration_engine.models import (
    Blueprint,
    ConflictStrategy,
    FileJoin,
    FileSource,
    MasterMigrationBlueprint,
    TableJoin,
    TableSource,
)
from migration_engine.validators.validation_result import ValidationReport

_STRATEGIES_REQUIRING_PRIMARY_KEYS = frozenset(
    {
        ConflictStrategy.UPSERT,
        ConflictStrategy.IGNORE_AND_LOG,
        ConflictStrategy.IGNORE_AND_INSERT_UNPROCESSED,
    }
)


class SchemaValidator:
    """Validates blueprint structure and cross-field business rules."""

    def validate(self, blueprint: MasterMigrationBlueprint) -> ValidationReport:
        report = ValidationReport(migration_id=blueprint.migration_id, is_valid=True)
        self._validate_blueprints_present(blueprint, report)
        self._validate_sequence_orders(blueprint, report)

        for bp in blueprint.blueprints:
            self._validate_chunking(bp, report)
            self._validate_target(bp, report)
            self._validate_sources(bp, report)
            self._validate_mappings(bp, report)

        return report

    def _validate_blueprints_present(
        self, blueprint: MasterMigrationBlueprint, report: ValidationReport
    ) -> None:
        if not blueprint.blueprints:
            report.add_issue("EMPTY_BLUEPRINTS", "At least one blueprint is required.", "blueprints")

    def _validate_sequence_orders(
        self, blueprint: MasterMigrationBlueprint, report: ValidationReport
    ) -> None:
        orders = [bp.sequence_order for bp in blueprint.blueprints]
        if len(orders) != len(set(orders)):
            report.add_issue(
                "DUPLICATE_SEQUENCE_ORDER",
                "Each blueprint must have a unique sequence_order.",
                "blueprints",
            )

        if orders and sorted(orders) != list(range(1, len(orders) + 1)):
            report.add_issue(
                "INVALID_SEQUENCE_ORDER",
                "sequence_order values must be contiguous starting at 1.",
                "blueprints",
            )

    def _validate_chunking(self, bp: Blueprint, report: ValidationReport) -> None:
        chunking = bp.chunking_strategy
        if not chunking.is_enabled:
            return

        if not chunking.chunk_by_column:
            report.add_issue(
                "CHUNK_COLUMN_REQUIRED",
                "chunk_by_column is required when chunking is enabled.",
                "chunking_strategy.chunk_by_column",
                bp.sequence_order,
            )
        if chunking.chunk_size is None or chunking.chunk_size <= 0:
            report.add_issue(
                "CHUNK_SIZE_REQUIRED",
                "chunk_size must be a positive integer when chunking is enabled.",
                "chunking_strategy.chunk_size",
                bp.sequence_order,
            )

    def _validate_target(self, bp: Blueprint, report: ValidationReport) -> None:
        target = bp.target

        if target.on_conflict in _STRATEGIES_REQUIRING_PRIMARY_KEYS and not target.primary_keys:
            report.add_issue(
                "PRIMARY_KEYS_REQUIRED",
                f"primary_keys are required for on_conflict strategy '{target.on_conflict.value}'.",
                "target.primary_keys",
                bp.sequence_order,
            )

        if (
            target.on_conflict == ConflictStrategy.IGNORE_AND_INSERT_UNPROCESSED
            and not target.unprocessed_table
        ):
            report.add_issue(
                "UNPROCESSED_TABLE_REQUIRED",
                "unprocessed_table is required for IGNORE_AND_INSERT_UNPROCESSED.",
                "target.unprocessed_table",
                bp.sequence_order,
            )

        if not bp.mappings:
            report.add_issue(
                "EMPTY_MAPPINGS",
                "At least one column mapping is required.",
                "mappings",
                bp.sequence_order,
            )

    def _validate_sources(self, bp: Blueprint, report: ValidationReport) -> None:
        root = bp.sources.root_table
        if isinstance(root, TableSource):
            if not root.schema or not root.table_name:
                report.add_issue(
                    "INVALID_ROOT_TABLE",
                    "Table root sources require schema and table_name.",
                    "sources.root_table",
                    bp.sequence_order,
                )
        elif isinstance(root, FileSource):
            if not root.file_name:
                report.add_issue(
                    "INVALID_ROOT_FILE",
                    "File root sources require file_name.",
                    "sources.root_table",
                    bp.sequence_order,
                )

        for index, join in enumerate(bp.sources.joins):
            path = f"sources.joins[{index}]"
            if isinstance(join, TableJoin):
                if not join.schema or not join.table_name:
                    report.add_issue(
                        "INVALID_JOIN_TABLE",
                        "Table joins require schema and table_name.",
                        path,
                        bp.sequence_order,
                    )
            elif isinstance(join, FileJoin) and not join.file_name:
                report.add_issue(
                    "INVALID_JOIN_FILE",
                    "File joins require file_name.",
                    path,
                    bp.sequence_order,
                )

            if not join.conditions:
                report.add_issue(
                    "EMPTY_JOIN_CONDITIONS",
                    "Each join must define at least one condition.",
                    f"{path}.conditions",
                    bp.sequence_order,
                )

    def _validate_mappings(self, bp: Blueprint, report: ValidationReport) -> None:
        target_columns: set[str] = set()
        for index, mapping in enumerate(bp.mappings):
            if mapping.target_column in target_columns:
                report.add_issue(
                    "DUPLICATE_TARGET_COLUMN",
                    f"Duplicate target_column '{mapping.target_column}'.",
                    f"mappings[{index}].target_column",
                    bp.sequence_order,
                )
            target_columns.add(mapping.target_column)

            if not mapping.cast_to.strip():
                report.add_issue(
                    "EMPTY_CAST_TYPE",
                    "cast_to must not be empty.",
                    f"mappings[{index}].cast_to",
                    bp.sequence_order,
                )
