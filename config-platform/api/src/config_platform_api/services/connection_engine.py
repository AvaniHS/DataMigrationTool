"""Create SQLAlchemy engines from stored connector records."""

from sqlalchemy.engine import Engine

from config_platform_api.connectors.registry import connector_registry
from config_platform_api.models.connections import ConnectionRecord
from config_platform_api.models.enums import ConnectionType


def create_engine_for_record(record: ConnectionRecord, *, connect_timeout: int = 10) -> Engine:
    connector = connector_registry.get(record.connector_id)
    if connector.export_type in {ConnectionType.CSV_S3_BUCKET.value, ConnectionType.LOCAL_CSV.value}:
        raise ValueError("File connectors do not use SQLAlchemy engines.")
    validated = connector.validate(record.connector_payload)
    return connector.create_engine(validated)


def export_type_for_record(record: ConnectionRecord) -> ConnectionType:
    connector = connector_registry.get(record.connector_id)
    return ConnectionType(connector.export_type)


def dispose_engine(engine: Engine | None) -> None:
    from config_platform_api.connectors.sql_helpers import dispose_sql_engine

    dispose_sql_engine(engine)
