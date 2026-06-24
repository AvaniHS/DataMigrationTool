"""Orchestrate connection lookup and target DDL operations."""

from config_platform_api.config import Settings
from config_platform_api.exceptions import DdlError, IntrospectionError
from config_platform_api.logging_setup import get_logger
from config_platform_api.models.table_ddl import CopyStructureMode, CopyStructureRequest, CopyStructureResponse
from config_platform_api.services.connection_engine import (
    create_engine_for_record,
    dispose_engine,
    export_type_for_record,
)
from config_platform_api.services.table_ddl_service import (
    copy_table_structure as run_copy_table_structure,
    create_audit_table,
    table_exists,
)
from config_platform_api.storage.connection_store import ConnectionNotFoundError, ConnectionStore

logger = get_logger(__name__)


def execute_copy_structure(
    connection_store: ConnectionStore,
    connection_ref: str,
    request: CopyStructureRequest,
    settings: Settings,
) -> CopyStructureResponse:
    normalized_ref = connection_ref.strip()
    qualified_name = f"{request.destination_schema}.{request.destination_table}"

    if settings.use_mock_introspection:
        return CopyStructureResponse(
            connection_ref=normalized_ref,
            mode=request.mode,
            qualified_name=qualified_name,
            created=True,
            skipped_existing=False,
            message="Mock mode: table creation simulated successfully.",
        )

    record = _get_connection(connection_store, normalized_ref)
    export_type = export_type_for_record(record)

    engine = None
    try:
        engine = create_engine_for_record(record)

        if table_exists(engine, export_type, request.destination_schema, request.destination_table):
            return CopyStructureResponse(
                connection_ref=normalized_ref,
                mode=request.mode,
                qualified_name=qualified_name,
                created=False,
                skipped_existing=True,
                message=f"Table {qualified_name} already exists on the target connection.",
            )

        if request.mode == CopyStructureMode.COPY_FROM_TABLE:
            run_copy_table_structure(
                engine,
                export_type,
                source_schema=request.source_schema or "",
                source_table=request.source_table or "",
                destination_schema=request.destination_schema,
                destination_table=request.destination_table,
            )
            message = (
                f"Created {qualified_name} by copying structure from "
                f"{request.source_schema}.{request.source_table}."
            )
        else:
            create_audit_table(
                engine,
                export_type,
                destination_schema=request.destination_schema,
                destination_table=request.destination_table,
                migration_id=request.migration_id or "",
                blueprint_sequence=request.blueprint_sequence or 1,
                target_schema=request.target_schema or "",
                target_table=request.target_table or "",
                primary_key_columns=request.primary_key_columns,
                target_columns=request.target_columns,
            )
            message = f"Created audit table {qualified_name} on the target connection."

        logger.info(
            "copy_structure_succeeded",
            connection_ref=normalized_ref,
            mode=request.mode.value,
            qualified_name=qualified_name,
        )
        return CopyStructureResponse(
            connection_ref=normalized_ref,
            mode=request.mode,
            qualified_name=qualified_name,
            created=True,
            skipped_existing=False,
            message=message,
        )
    except DdlError:
        raise
    except Exception as exc:
        logger.warning(
            "copy_structure_failed",
            connection_ref=normalized_ref,
            mode=request.mode.value,
            qualified_name=qualified_name,
            error=str(exc),
            exc_info=True,
        )
        raise DdlError(_sanitize_error(str(exc))) from exc
    finally:
        dispose_engine(engine)


def _get_connection(connection_store: ConnectionStore, connection_ref: str):
    try:
        return connection_store.get(connection_ref)
    except ConnectionNotFoundError as exc:
        raise IntrospectionError(str(exc)) from exc


def _sanitize_error(message: str) -> str:
    lowered = message.lower()
    if "password" in lowered or "access denied" in lowered or "permission" in lowered:
        return "Unable to create table on target. Check credentials and DDL permissions."
    if len(message) > 240:
        return f"{message[:237]}..."
    return message
