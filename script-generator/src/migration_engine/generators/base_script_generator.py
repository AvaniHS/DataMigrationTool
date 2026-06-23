"""Script generator interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from migration_engine.models import MasterMigrationBlueprint


@dataclass(frozen=True)
class GeneratedScript:
    """Output artifact from a script generator."""

    content: str
    migration_id: str
    output_format: str


class IScriptGenerator(ABC):
    """Produces migration output from a validated blueprint."""

    @abstractmethod
    def generate(self, blueprint: MasterMigrationBlueprint) -> GeneratedScript:
        """Compile the blueprint into an output script."""
