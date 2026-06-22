"""Whitelist-based SQL expression validation."""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from migration_engine.models import Blueprint, MasterMigrationBlueprint
from migration_engine.validators.validation_result import ValidationReport

_FUNCTION_CALL_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_ALIAS_REFERENCE_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\.")

_DEFAULT_WHITELIST_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "whitelists" / "mysql_expressions.yaml"
)


@dataclass(frozen=True)
class ExpressionWhitelist:
    functions: frozenset[str]
    keywords: frozenset[str]
    operators: frozenset[str]
    allowed_cast_types: frozenset[str]


_ALLOWED_LITERAL_CHARS = frozenset(" _().,'\"`[]")


class ExpressionValidator:
    """Validates SQL fragments against a dialect expression whitelist."""

    def __init__(self, whitelist_path: Path | None = None) -> None:
        path = whitelist_path or _DEFAULT_WHITELIST_PATH
        self._whitelist = self._load_whitelist(path)

    def validate(self, blueprint: MasterMigrationBlueprint) -> ValidationReport:
        report = ValidationReport(migration_id=blueprint.migration_id, is_valid=True)

        for bp in blueprint.blueprints:
            self._validate_filters(bp.pre_filters, "pre_filters", bp.sequence_order, report)
            self._validate_filters(bp.post_filters, "post_filters", bp.sequence_order, report)

            for index, derivation in enumerate(bp.derivations):
                self._validate_expression(
                    derivation.expression,
                    f"derivations[{index}].expression",
                    bp.sequence_order,
                    report,
                )
                self._validate_identifier(
                    derivation.variable_name,
                    f"derivations[{index}].variable_name",
                    bp.sequence_order,
                    report,
                )

            for index, mapping in enumerate(bp.mappings):
                self._validate_cast_type(
                    mapping.cast_to,
                    f"mappings[{index}].cast_to",
                    bp.sequence_order,
                    report,
                )
                if mapping.source_type.value in {"EXPRESSION", "CONSTANT", "DIRECT", "DERIVED"}:
                    self._validate_mapping_source(
                        mapping.source_type.value,
                        mapping.source_value,
                        f"mappings[{index}].source_value",
                        bp.sequence_order,
                        report,
                    )

            self._validate_join_expressions(bp, report)

        return report

    def _load_whitelist(self, path: Path) -> ExpressionWhitelist:
        if not path.is_file():
            raise FileNotFoundError(f"Expression whitelist not found: {path}")

        with path.open(encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)

        return ExpressionWhitelist(
            functions=frozenset(str(item).upper() for item in raw.get("functions", [])),
            keywords=frozenset(str(item).upper() for item in raw.get("keywords", [])),
            operators=frozenset(str(item) for item in raw.get("operators", [])),
            allowed_cast_types=frozenset(
                str(item).upper() for item in raw.get("allowed_cast_types", [])
            ),
        )

    def _validate_join_expressions(self, bp: Blueprint, report: ValidationReport) -> None:
        for join_index, join in enumerate(bp.sources.joins):
            for cond_index, condition in enumerate(join.conditions):
                base = f"sources.joins[{join_index}].conditions[{cond_index}]"
                self._validate_expression(
                    condition.left_expression,
                    f"{base}.left_expression",
                    bp.sequence_order,
                    report,
                )
                self._validate_expression(
                    condition.right_expression,
                    f"{base}.right_expression",
                    bp.sequence_order,
                    report,
                )
                self._validate_operator(
                    condition.operator,
                    f"{base}.operator",
                    bp.sequence_order,
                    report,
                )

    def _validate_filters(
        self,
        filters: list[str],
        field_name: str,
        sequence_order: int,
        report: ValidationReport,
    ) -> None:
        for index, expression in enumerate(filters):
            self._validate_expression(
                expression,
                f"{field_name}[{index}]",
                sequence_order,
                report,
            )

    def _validate_mapping_source(
        self,
        source_type: str,
        source_value: str,
        path: str,
        sequence_order: int,
        report: ValidationReport,
    ) -> None:
        if source_type == "DERIVED":
            if not source_value.startswith("derivations."):
                report.add_issue(
                    "INVALID_DERIVED_REFERENCE",
                    "DERIVED mappings must use 'derivations.<variable_name>' format.",
                    path,
                    sequence_order,
                )
            return

        if source_type == "CONSTANT":
            return

        self._validate_expression(source_value, path, sequence_order, report)

    def _validate_expression(
        self,
        expression: str,
        path: str,
        sequence_order: int,
        report: ValidationReport,
    ) -> None:
        if not expression.strip():
            report.add_issue("EMPTY_EXPRESSION", "SQL expression must not be empty.", path, sequence_order)
            return

        for match in _FUNCTION_CALL_PATTERN.finditer(expression):
            function_name = match.group(1).upper()
            if function_name in self._whitelist.keywords:
                continue
            if function_name not in self._whitelist.functions:
                report.add_issue(
                    "DISALLOWED_FUNCTION",
                    f"Function '{function_name}' is not in the expression whitelist.",
                    path,
                    sequence_order,
                )

        if not self._operators_allowed(expression):
            report.add_issue(
                "DISALLOWED_OPERATOR",
                "Expression contains operators that are not whitelisted.",
                path,
                sequence_order,
            )

    def _operators_allowed(self, expression: str) -> bool:
        index = 0
        while index < len(expression):
            quote = expression[index]
            if quote in {"'", '"'}:
                index = self._skip_quoted_literal(expression, index, quote)
                continue

            matched = False
            for operator in sorted(self._whitelist.operators, key=len, reverse=True):
                if expression.startswith(operator, index):
                    index += len(operator)
                    matched = True
                    break

            if matched:
                continue

            character = expression[index]
            if character.isalnum() or character in _ALLOWED_LITERAL_CHARS:
                index += 1
                continue

            return False

        return True

    def _skip_quoted_literal(self, expression: str, start: int, quote: str) -> int:
        index = start + 1
        while index < len(expression):
            if expression[index] != quote:
                index += 1
                continue

            if index + 1 < len(expression) and expression[index + 1] == quote:
                index += 2
                continue

            return index + 1

        return index

    def _validate_operator(
        self,
        operator: str,
        path: str,
        sequence_order: int,
        report: ValidationReport,
    ) -> None:
        if operator not in self._whitelist.operators:
            report.add_issue(
                "DISALLOWED_OPERATOR",
                f"Operator '{operator}' is not in the whitelist.",
                path,
                sequence_order,
            )

    def _validate_cast_type(
        self,
        cast_to: str,
        path: str,
        sequence_order: int,
        report: ValidationReport,
    ) -> None:
        base_type = cast_to.split("(", 1)[0].strip().upper()
        if base_type not in self._whitelist.allowed_cast_types:
            report.add_issue(
                "DISALLOWED_CAST_TYPE",
                f"Cast type '{cast_to}' is not allowed for the target dialect.",
                path,
                sequence_order,
            )

    def _validate_identifier(
        self,
        identifier: str,
        path: str,
        sequence_order: int,
        report: ValidationReport,
    ) -> None:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
            report.add_issue(
                "INVALID_IDENTIFIER",
                f"Identifier '{identifier}' is not a valid SQL alias/name.",
                path,
                sequence_order,
            )

    def extract_aliases(self, expression: str) -> set[str]:
        """Return table aliases referenced as alias.column in an expression."""
        return set(_ALIAS_REFERENCE_PATTERN.findall(expression))
