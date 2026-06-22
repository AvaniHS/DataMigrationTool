"""Migration executor interface — Phase C."""

from abc import ABC, abstractmethod
from pathlib import Path


class IExecutor(ABC):
    """Runs generated migration scripts against a target environment."""

    @abstractmethod
    def execute(self, script_path: Path) -> None:
        """Execute the script and emit structured telemetry."""
