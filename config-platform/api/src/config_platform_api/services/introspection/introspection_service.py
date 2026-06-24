"""Orchestrate connection lookup and schema introspection."""

from config_platform_api.config import Settings
from config_platform_api.connectors.payloads import LocalCsvConnectorPayload, S3BucketConnectorPayload
from config_platform_api.exceptions import IntrospectionError
from config_platform_api.logging_setup import get_logger
from config_platform_api.models.enums import ConnectionType
from config_platform_api.models.introspection import ColumnNode, SchemaNode, S3FileNode, TableNode
from config_platform_api.services.connection_engine import (
    create_engine_for_record,
    dispose_engine,
    export_type_for_record,
)
from config_platform_api.services.introspection import database_introspector, local_csv_introspector, mock_catalog, s3_introspector
from config_platform_api.services.local_csv.resolver import resolve_csv_path
from config_platform_api.storage.connection_store import ConnectionNotFoundError, ConnectionStore
from config_platform_api.storage.staging_store import StagingStore

logger = get_logger(__name__)


def list_schemas(
    connection_store: ConnectionStore,
    connection_ref: str,
    settings: Settings,
) -> list[SchemaNode]:
    if settings.use_mock_introspection:
        return mock_catalog.mock_list_schemas()

    record = _get_connection(connection_store, connection_ref)
    export_type = export_type_for_record(record)
    if export_type == ConnectionType.CSV_S3_BUCKET:
        raise IntrospectionError("S3 connections do not expose SQL schemas. Use /files instead.")
    if export_type == ConnectionType.LOCAL_CSV:
        raise IntrospectionError("Local CSV connections do not expose SQL schemas. Use /files instead.")

    engine = None
    try:
        engine = create_engine_for_record(record)
        return database_introspector.list_schemas(engine, export_type)
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
    export_type = export_type_for_record(record)
    if export_type == ConnectionType.CSV_S3_BUCKET:
        raise IntrospectionError("S3 connections do not expose SQL tables.")

    engine = None
    try:
        engine = create_engine_for_record(record)
        return database_introspector.list_tables(engine, export_type, schema)
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
    export_type = export_type_for_record(record)
    if export_type == ConnectionType.CSV_S3_BUCKET:
        raise IntrospectionError("S3 connections do not expose SQL columns.")

    engine = None
    try:
        engine = create_engine_for_record(record)
        return database_introspector.list_columns(engine, export_type, schema, table)
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
    staging_store: StagingStore | None = None,
) -> list[S3FileNode]:
    if settings.use_mock_introspection:
        return mock_catalog.mock_list_s3_files()

    record = _get_connection(connection_store, connection_ref)
    export_type = export_type_for_record(record)
    if export_type == ConnectionType.LOCAL_CSV:
        return _list_local_csv_files(record, connection_ref, settings, staging_store)
    if export_type != ConnectionType.CSV_S3_BUCKET:
        raise IntrospectionError("File listing is only available for file connections.")

    s3 = S3BucketConnectorPayload.model_validate(record.connector_payload)

    try:
        return s3_introspector.list_s3_files(s3)
    except Exception as exc:
        logger.warning(
            "introspection_files_failed",
            connection_ref=connection_ref,
            error=str(exc),
            exc_info=True,
        )
        raise IntrospectionError(_sanitize_error(str(exc))) from exc


def list_file_columns(
    connection_store: ConnectionStore,
    connection_ref: str,
    file_name: str,
    settings: Settings,
    staging_store: StagingStore | None = None,
) -> list[ColumnNode]:
    if settings.use_mock_introspection:
        return mock_catalog.mock_list_columns("files", file_name)

    record = _get_connection(connection_store, connection_ref)
    export_type = export_type_for_record(record)
    if export_type == ConnectionType.CSV_S3_BUCKET:
        s3 = S3BucketConnectorPayload.model_validate(record.connector_payload)
        try:
            return s3_introspector.list_s3_file_columns(s3, file_name)
        except Exception as exc:
            logger.warning(
                "introspection_s3_file_columns_failed",
                connection_ref=connection_ref,
                file_name=file_name,
                error=str(exc),
                exc_info=True,
            )
            raise IntrospectionError(_sanitize_error(str(exc))) from exc
    if export_type != ConnectionType.LOCAL_CSV:
        raise IntrospectionError("Column preview from files is only available for file connections.")

    try:
        path = _resolve_local_csv_path(record, connection_ref, settings, staging_store)
        if path.name != file_name:
            raise IntrospectionError(f"File '{file_name}' was not found for this connection.")
        payload = LocalCsvConnectorPayload.model_validate(record.connector_payload)
        return local_csv_introspector.list_local_csv_columns(path, payload.parse_options.model_dump())
    except IntrospectionError:
        raise
    except Exception as exc:
        logger.warning(
            "introspection_file_columns_failed",
            connection_ref=connection_ref,
            file_name=file_name,
            error=str(exc),
            exc_info=True,
        )
        raise IntrospectionError(_sanitize_error(str(exc))) from exc


def _list_local_csv_files(
    record,
    connection_ref: str,
    settings: Settings,
    staging_store: StagingStore | None,
) -> list[S3FileNode]:
    try:
        path = _resolve_local_csv_path(record, connection_ref, settings, staging_store)
        return local_csv_introspector.list_local_csv_files(path)
    except Exception as exc:
        logger.warning(
            "introspection_local_csv_files_failed",
            connection_ref=connection_ref,
            error=str(exc),
            exc_info=True,
        )
        raise IntrospectionError(_sanitize_error(str(exc))) from exc


def _resolve_local_csv_path(record, connection_ref: str, settings: Settings, staging_store: StagingStore | None):
    resolved_staging = staging_store or StagingStore(settings.staging_dir)
    payload = LocalCsvConnectorPayload.model_validate(record.connector_payload)
    return resolve_csv_path(
        {
            **payload.model_dump(),
            "parse_options": payload.parse_options.model_dump(),
        },
        settings=settings,
        staging_store=resolved_staging,
        connection_ref=connection_ref,
    )


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
