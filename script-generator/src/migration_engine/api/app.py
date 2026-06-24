"""Minimal HTTP API for config-platform validate proxy."""

from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict

from migration_engine.parsers.blueprint_parser import BlueprintParseError
from migration_engine.validation_service import validate_migration_payload

app = FastAPI(title="Migration Engine API", version="0.1.0")


class ValidateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    migration_id: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/validate")
def validate_endpoint(body: dict[str, Any]) -> dict[str, Any]:
    try:
        return validate_migration_payload(body)
    except BlueprintParseError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
