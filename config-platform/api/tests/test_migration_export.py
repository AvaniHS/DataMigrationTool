"""Unit tests for migration export assembly."""

from datetime import UTC, datetime
from pathlib import Path

from config_platform_api.models.connections import ConnectionSaveRequest
from config_platform_api.models.enums import OnConflictStrategy
from config_platform_api.models.migrations import (
    Blueprint,
    BlueprintSources,
    BlueprintTarget,
    ColumnMapping,
    MigrationRecord,
    RootTableSource,
)
from config_platform_api.services.migration_export import (
    assemble_migration_export,
    blueprint_to_export_dict,
    collect_connection_refs,
)
from config_platform_api.storage.connection_store import ConnectionStore


def _save_mysql_connection(store: ConnectionStore, ref: str = "client_crm_mysql") -> None:
    store.create(
        ConnectionSaveRequest(
            ref=ref,
            connector_id="mysql",
            connector_payload={
                "auth_method": "password",
                "host": "client-crm-ip",
                "port": 3306,
                "database": "crm_db",
                "username": "read_user",
                "password": "pass",
                "use_advanced_string": False,
            },
            verification_token="verified",
        ),
        tested_at=datetime.now(UTC),
    )


def test_collect_connection_refs_includes_target_and_sources() -> None:
    migration = MigrationRecord(
        migration_id="mig_test",
        client_id="client",
        version="1.0.0",
        blueprints=[
            Blueprint(
                sequence_order=1,
                target=BlueprintTarget(
                    connection_ref="target_db",
                    schema_name="core",
                    table_name="customers",
                    primary_keys=["id"],
                    on_conflict=OnConflictStrategy.UPSERT,
                ),
                sources=BlueprintSources(
                    root_table=RootTableSource(
                        connection_ref="src_db",
                        alias="cm",
                        schema_name="crm",
                        table_name="customers",
                    ),
                    joins=[],
                ),
            ),
        ],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    assert collect_connection_refs(migration) == {"target_db", "src_db"}


def test_blueprint_to_export_dict_omits_empty_file_fields() -> None:
    blueprint = Blueprint(
        sequence_order=1,
        target=BlueprintTarget(),
        sources=BlueprintSources(
            root_table=RootTableSource(
                connection_ref="client_archival_s3",
                alias="hih",
                file_name="headers.csv",
            ),
            joins=[],
        ),
    )
    exported = blueprint_to_export_dict(blueprint)
    root = exported["sources"]["root_table"]
    assert root["file_name"] == "headers.csv"
    assert "schema" not in root
    assert "table_name" not in root


def test_assemble_migration_export_matches_contract_shape(tmp_path: Path) -> None:
    connection_store = ConnectionStore(tmp_path / "connections.json")
    _save_mysql_connection(connection_store)

    migration = MigrationRecord(
        migration_id="mig_export_test",
        client_id="client_acme",
        version="1.0.0",
        blueprints=[
            Blueprint(
                sequence_order=1,
                target=BlueprintTarget(
                    connection_ref="client_crm_mysql",
                    schema_name="core",
                    table_name="customers",
                    primary_keys=["id"],
                    on_conflict=OnConflictStrategy.UPSERT,
                ),
                sources=BlueprintSources(
                    root_table=RootTableSource(
                        connection_ref="client_crm_mysql",
                        alias="cm",
                        schema_name="crm_db",
                        table_name="customer_master",
                    ),
                    joins=[],
                ),
                mappings=[
                    ColumnMapping(
                        target_column="id",
                        source_type="DIRECT",
                        source_value="cm.id",
                        cast_to="INT",
                        is_nullable=False,
                    ),
                ],
            ),
        ],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    exported = assemble_migration_export(migration, connection_store)
    assert exported["migration_id"] == "mig_export_test"
    assert exported["output_format"] == "SQL"
    assert "client_crm_mysql" in exported["connections"]
    assert exported["connections"]["client_crm_mysql"]["type"] == "MYSQL"
    assert exported["blueprints"][0]["target"]["schema"] == "core"
    assert exported["blueprints"][0]["mappings"][0]["target_column"] == "id"
