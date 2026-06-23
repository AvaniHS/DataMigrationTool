"""Connection reference and alias graph validation."""

from migration_engine.models import Blueprint, MasterMigrationBlueprint, SourceType
from migration_engine.models.enums import ConnectionType, DialectType
from migration_engine.validators.expression_validator import ExpressionValidator
from migration_engine.validators.validation_result import ValidationReport

_MYSQL_V1_SUPPORTED_SOURCES = frozenset(
    {
        ConnectionType.MYSQL,
        ConnectionType.MSSQL,
        ConnectionType.POSTGRESQL,
        ConnectionType.CSV_S3_BUCKET,
    }
)


class ConnectivityValidator:
    """Validates connection references, aliases, and dialect connectivity rules."""

    def __init__(self, compile_dialect: DialectType = DialectType.MYSQL) -> None:
        self._compile_dialect = compile_dialect
        self._expression_validator = ExpressionValidator()

    def validate(self, blueprint: MasterMigrationBlueprint) -> ValidationReport:
        report = ValidationReport(migration_id=blueprint.migration_id, is_valid=True)
        connection_names = set(blueprint.connections)

        for bp in blueprint.blueprints:
            self._validate_connection_refs(bp, connection_names, report)
            aliases = self._collect_aliases(bp)
            self._validate_alias_uniqueness(bp, aliases, report)
            self._validate_join_aliases(bp, aliases, report)
            self._validate_derivation_references(bp, report)
            self._validate_chunk_alias(bp, aliases, report)
            self._validate_source_types(bp, blueprint, report)

        return report

    def _validate_connection_refs(
        self,
        bp: Blueprint,
        connection_names: set[str],
        report: ValidationReport,
    ) -> None:
        refs = {bp.target.connection_ref, bp.sources.root_table.connection_ref}
        refs.update(join.connection_ref for join in bp.sources.joins)

        for ref in refs:
            if ref not in connection_names:
                report.add_issue(
                    "UNKNOWN_CONNECTION_REF",
                    f"Connection reference '{ref}' is not defined in connections.",
                    "connections",
                    bp.sequence_order,
                )

    def _collect_aliases(self, bp: Blueprint) -> set[str]:
        aliases = {bp.sources.root_table.alias}
        aliases.update(join.alias for join in bp.sources.joins)
        return aliases

    def _validate_alias_uniqueness(
        self,
        bp: Blueprint,
        aliases: set[str],
        report: ValidationReport,
    ) -> None:
        declared: list[str] = [bp.sources.root_table.alias]
        declared.extend(join.alias for join in bp.sources.joins)

        if len(declared) != len(set(declared)):
            report.add_issue(
                "DUPLICATE_ALIAS",
                "Source aliases must be unique within a blueprint.",
                "sources",
                bp.sequence_order,
            )

        if aliases != set(declared):
            report.add_issue(
                "INVALID_ALIAS_SET",
                "Alias collection does not match declared sources.",
                "sources",
                bp.sequence_order,
            )

    def _validate_join_aliases(
        self,
        bp: Blueprint,
        aliases: set[str],
        report: ValidationReport,
    ) -> None:
        for join_index, join in enumerate(bp.sources.joins):
            for cond_index, condition in enumerate(join.conditions):
                path = f"sources.joins[{join_index}].conditions[{cond_index}]"
                for side, expression in (
                    ("left", condition.left_expression),
                    ("right", condition.right_expression),
                ):
                    referenced = self._expression_validator.extract_aliases(expression)
                    unknown = referenced - aliases
                    if unknown:
                        report.add_issue(
                            "UNKNOWN_ALIAS",
                            f"{side} expression references unknown alias(es): "
                            f"{', '.join(sorted(unknown))}.",
                            path,
                            bp.sequence_order,
                        )

    def _validate_derivation_references(self, bp: Blueprint, report: ValidationReport) -> None:
        derivation_names = {item.variable_name for item in bp.derivations}

        for index, mapping in enumerate(bp.mappings):
            if mapping.source_type != SourceType.DERIVED:
                continue

            prefix = "derivations."
            if not mapping.source_value.startswith(prefix):
                continue

            variable_name = mapping.source_value[len(prefix) :]
            if variable_name not in derivation_names:
                report.add_issue(
                    "UNKNOWN_DERIVATION",
                    f"Mapping references unknown derivation '{variable_name}'.",
                    f"mappings[{index}].source_value",
                    bp.sequence_order,
                )

    def _validate_chunk_alias(
        self,
        bp: Blueprint,
        aliases: set[str],
        report: ValidationReport,
    ) -> None:
        if not bp.chunking_strategy.is_enabled or not bp.chunking_strategy.chunk_by_column:
            return

        referenced = self._expression_validator.extract_aliases(bp.chunking_strategy.chunk_by_column)
        if not referenced:
            report.add_issue(
                "CHUNK_ALIAS_REQUIRED",
                "chunk_by_column must be qualified as alias.column.",
                "chunking_strategy.chunk_by_column",
                bp.sequence_order,
            )
            return

        unknown = referenced - aliases
        if unknown:
            report.add_issue(
                "UNKNOWN_CHUNK_ALIAS",
                f"chunk_by_column references unknown alias(es): {', '.join(sorted(unknown))}.",
                "chunking_strategy.chunk_by_column",
                bp.sequence_order,
            )

    def _validate_source_types(
        self,
        bp: Blueprint,
        blueprint: MasterMigrationBlueprint,
        report: ValidationReport,
    ) -> None:
        if self._compile_dialect != DialectType.MYSQL:
            return

        refs = {bp.target.connection_ref, bp.sources.root_table.connection_ref}
        refs.update(join.connection_ref for join in bp.sources.joins)

        for ref in refs:
            if ref not in blueprint.connections:
                continue

            connection = blueprint.connections[ref]
            if connection.type not in _MYSQL_V1_SUPPORTED_SOURCES:
                report.add_issue(
                    "UNSUPPORTED_SOURCE_TYPE",
                    f"Connection '{ref}' type '{connection.type}' is not supported for "
                    f"MySQL script generation in v1.",
                    f"connections.{ref}.type",
                    bp.sequence_order,
                )
