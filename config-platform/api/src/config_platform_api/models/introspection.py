from pydantic import BaseModel, ConfigDict, Field


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SchemaNode(_StrictModel):
    name: str


class TableNode(_StrictModel):
    name: str
    schema_name: str = Field(serialization_alias="schema")
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, populate_by_name=True)


class ColumnNode(_StrictModel):
    name: str
    data_type: str
    is_nullable: bool


class S3FileNode(_StrictModel):
    name: str
    key: str
    size_bytes: int | None = None
    last_modified: str | None = None
