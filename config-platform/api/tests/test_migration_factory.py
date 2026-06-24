import pytest

from config_platform_api.models.migrations import Blueprint, BlueprintTarget
from config_platform_api.services.migration_factory import (
    create_empty_blueprint,
    duplicate_blueprint,
    normalize_blueprint_sequence,
)


def test_create_empty_blueprint_has_defaults() -> None:
    blueprint = create_empty_blueprint(1)
    assert blueprint.sequence_order == 1
    assert blueprint.target.on_conflict == "FAIL"
    assert blueprint.sources.root_table.alias == "src"


def test_duplicate_blueprint_assigns_new_sequence() -> None:
    source = create_empty_blueprint(1).model_copy(
        update={"target": BlueprintTarget.model_validate({"schema": "core", "table_name": "customers"})},
    )
    duplicate = duplicate_blueprint(source, 2)
    assert duplicate.sequence_order == 2
    assert duplicate.target.table_name == "customers"
    assert duplicate is not source


def test_normalize_blueprint_sequence_renumbers() -> None:
    blueprints = [
        Blueprint(sequence_order=3, target=BlueprintTarget()),
        Blueprint(sequence_order=1, target=BlueprintTarget()),
    ]
    normalized = normalize_blueprint_sequence(blueprints)
    assert [item.sequence_order for item in normalized] == [1, 2]
