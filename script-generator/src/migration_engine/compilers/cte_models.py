"""CTE pipeline data models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CteStage:
    """A single named CTE in the pipeline."""

    name: str
    body: str
    comment: str = ""


@dataclass(frozen=True)
class CtePipeline:
    """Ordered CTE stages for one blueprint."""

    stages: tuple[CteStage, ...]
    projection_cte: str

    def render_with_clause(self) -> str:
        """Emit a WITH clause containing all pipeline CTEs."""
        if not self.stages:
            raise ValueError("Cannot render an empty CTE pipeline.")

        rendered_stages: list[str] = []
        for stage in self.stages:
            comment_line = f"  -- {stage.comment}\n" if stage.comment else ""
            indented_body = _indent(stage.body, spaces=4)
            rendered_stages.append(
                f"{comment_line}  {stage.name} AS (\n{indented_body}\n  )"
            )

        return "WITH\n" + ",\n".join(rendered_stages)


def _indent(text: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(f"{prefix}{line}" if line else prefix for line in text.splitlines())
