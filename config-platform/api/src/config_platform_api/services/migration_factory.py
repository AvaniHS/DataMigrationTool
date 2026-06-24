"""Factory helpers for migration and blueprint documents."""

import copy

from config_platform_api.models.enums import OnConflictStrategy
from config_platform_api.models.migrations import (
    Blueprint,
    BlueprintSources,
    BlueprintTarget,
    ChunkingStrategy,
    RootTableSource,
)


def create_empty_blueprint(sequence_order: int) -> Blueprint:
    return Blueprint(
        sequence_order=sequence_order,
        target=BlueprintTarget(on_conflict=OnConflictStrategy.FAIL),
        sources=BlueprintSources(root_table=RootTableSource()),
        chunking_strategy=ChunkingStrategy(),
        pre_filters=[],
        post_filters=[],
        derivations=[],
        mappings=[],
    )


def next_sequence_order(blueprints: list[Blueprint]) -> int:
    if not blueprints:
        return 1
    return max(item.sequence_order for item in blueprints) + 1


def duplicate_blueprint(blueprint: Blueprint, sequence_order: int) -> Blueprint:
    copied = copy.deepcopy(blueprint.model_dump())
    copied["sequence_order"] = sequence_order
    return Blueprint.model_validate(copied)


def normalize_blueprint_sequence(blueprints: list[Blueprint]) -> list[Blueprint]:
    ordered = sorted(blueprints, key=lambda item: item.sequence_order)
    return [
        blueprint.model_copy(update={"sequence_order": index})
        for index, blueprint in enumerate(ordered, start=1)
    ]
