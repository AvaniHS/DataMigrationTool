"""Resolves mapping source values to SQL projection expressions."""

from migration_engine.models.enums import SourceType
from migration_engine.models.mapping import ColumnMapping

_DERIVATION_PREFIX = "derivations."


def resolve_mapping_expression(mapping: ColumnMapping) -> str:
    """Return the raw SQL expression for a mapping before safe casting."""
    if mapping.source_type == SourceType.DERIVED:
        if not mapping.source_value.startswith(_DERIVATION_PREFIX):
            raise ValueError(
                f"DERIVED mapping '{mapping.target_column}' must reference "
                f"'{_DERIVATION_PREFIX}<variable_name>'."
            )
        return mapping.source_value[len(_DERIVATION_PREFIX) :]

    return mapping.source_value
