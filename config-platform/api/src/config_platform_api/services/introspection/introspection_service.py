"""Orchestrate connection lookup and schema introspection."""

from config_platform_api.config import Settings
from config_platform_api.exceptions import IntrospectionError
from config_platform_api.logging_setup import get_logger
from config_platform_api.models.enums import ConnectionType
from config_platform_api.models.introspection import ColumnNode, SchemaNode, S3FileNode, TableNode
from config_platform_api.services.connection_engine import create_engine_for_record, dispose_engine
from config_platform_api.services.introspection import database_introspector, mock_catalog, s3_introspector
from config_platform_api.storage.connection_store import ConnectionNotFoundError, ConnectionStore

logger = get_logger(__name__)


def list_schemas(
    connection_store: ConnectionStore,
    connection_ref: str,
    settings: Settings,
) -> list[SchemaNode]:
    if settings.use_mock_introspection:
        return mock_catalog.mock_list_schemas()

    record = _get_connection(connection_store, connection_ref)
    if record.type == ConnectionType.CSV_S3_BUCKET:
        raise IntrospectionError("S3 connections do not expose SQL schemas. Use /files instead.")

    engine = None
    try:
        engine = create_engine_for_record(record)
        return database_introspector.list_schemas(engine, record.type)
    except Exception as exc:
        logger.warning(
            "introspection_schemas_failed",
            connection_ref=connection_ref,
            error=str(exc),
            exc_info=True,
        )
        raise IntrospectionError(_sanitize_error(str(exc))) from exc
    finally:
        dispose_engine(engine)


def list_tables(
    connection_store: ConnectionStore,
    connection_ref: str,
    schema: str,
    settings: Settings,
) -> list[TableNode]:
    if settings.use_mock_introspection:
        return mock_catalog.mock_list_tables(schema)

    record = _get_connection(connection_store, connection_ref)
    if record.type == ConnectionType.CSV_S3_BUCKET:
        raise IntrospectionError("S3 connections do not expose SQL tables.")

    engine = None
    try:
        engine = create_engine_for_record(record)
        return database_introspector.list_tables(engine, record.type, schema)
    except Exception as exc:
        logger.warning(
            "introspection_tables_failed",
            connection_ref=connection_ref,
            schema=schema,
            error=str(exc),
            exc_info=True,
        )
        raise IntrospectionError(_sanitize_error(str(exc))) from exc
    finally:
        dispose_engine(engine)


def list_columns(
    connection_store: ConnectionStore,
    connection_ref: str,
    schema: str,
    table: str,
    settings: Settings,
) -> list[ColumnNode]:
    if settings.use_mock_introspection:
        return mock_catalog.mock_list_columns(schema, table)

    record = _get_connection(connection_store, connection_ref)
    if record.type == ConnectionType.CSV_S3_BUCKET:
        raise IntrospectionError("S3 connections do not expose SQL columns.")

    engine = None
    try:
        engine = create_engine_for_record(record)
        return database_introspector.list_columns(engine, record.type, schema, table)
    except Exception as exc:
        logger.warning(
            "introspection_columns_failed",
            connection_ref=connection_ref,
            schema=schema,
            table=table,
            error=str(exc),
            exc_info=True,
        )
        raise IntrospectionError(_sanitize_error(str(exc))) from exc
    finally:
        dispose_engine(engine)


def list_files(
    connection_store: ConnectionStore,
    connection_ref: str,
    settings: Settings,
) -> list[S3FileNode]:
    if settings.use_mock_introspection:
        return mock_catalog.mock_list_s3_files()

    record = _get_connection(connection_store, connection_ref)
    if record.type != ConnectionType.CSV_S3_BUCKET:
        raise IntrospectionError("File listing is only available for CSV_S3_BUCKET connections.")
    if record.s3 is None:
        raise IntrospectionError("S3 connection fields are missing.")

    try:
        return s3_introspector.list_s3_files(record.s3)
    except Exception as exc:
        logger.warning(
            "introspection_files_failed",
            connection_ref=connection_ref,
            error=str(exc),
            exc_info=True,
        )
        raise IntrospectionError(_sanitize_error(str(exc))) from exc


def _get_connection(connection_store: ConnectionStore, connection_ref: str):
    try:
        return connection_store.get(connection_ref)
    except ConnectionNotFoundError as exc:
        raise IntrospectionError(str(exc)) from exc


def _sanitize_error(message: str) -> str:
    lowered = message.lower()
    if "password" in lowered or "access denied" in lowered:
        return "Unable to read schema metadata. Check credentials and network access."
    if len(message) > 240:
        return f"{message[:237]}..."
    return message
