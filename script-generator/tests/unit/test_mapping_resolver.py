"""Unit tests for mapping expression resolution."""

import pytest

from migration_engine.compilers.mapping_resolver import resolve_mapping_expression
from migration_engine.models.enums import SourceType
from migration_engine.models.mapping import ColumnMapping


def test_resolve_direct_mapping() -> None:
    mapping = ColumnMapping(
        target_column="id",
        source_type=SourceType.DIRECT,
        source_value="cm.global_uuid",
        cast_to="UUID",
        is_nullable=False,
    )
    assert resolve_mapping_expression(mapping) == "cm.global_uuid"


def test_resolve_derived_mapping() -> None:
    mapping = ColumnMapping(
        target_column="phone",
        source_type=SourceType.DERIVED,
        source_value="derivations.formatted_phone",
        cast_to="VARCHAR(32)",
        is_nullable=True,
    )
    assert resolve_mapping_expression(mapping) == "formatted_phone"


def test_resolve_constant_mapping() -> None:
    mapping = ColumnMapping(
        target_column="tenant_id",
        source_type=SourceType.CONSTANT,
        source_value="'RETAIL_ENTERPRISE_GLOBAL'",
        cast_to="VARCHAR(64)",
        is_nullable=False,
    )
    assert resolve_mapping_expression(mapping) == "'RETAIL_ENTERPRISE_GLOBAL'"


def test_invalid_derived_reference_raises() -> None:
    mapping = ColumnMapping(
        target_column="phone",
        source_type=SourceType.DERIVED,
        source_value="formatted_phone",
        cast_to="VARCHAR(32)",
        is_nullable=True,
    )
    with pytest.raises(ValueError, match="derivations."):
        resolve_mapping_expression(mapping)
