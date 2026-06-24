"""Unit tests for table DDL statement builders."""

import pytest

from config_platform_api.exceptions import DdlError
from config_platform_api.models.enums import ConnectionType
from config_platform_api.models.table_ddl import TableColumnSpec
from config_platform_api.services.table_ddl_service import _build_audit_table_ddl, _build_copy_structure_ddl


def test_build_mysql_copy_structure_ddl() -> None:
    ddl = _build_copy_structure_ddl(
        ConnectionType.MYSQL,
        source_schema="core",
        source_table="customers",
        destination_schema="core",
        destination_table="customers_unprocessed",
    )
    assert ddl == "CREATE TABLE `core`.`customers_unprocessed` LIKE `core`.`customers`"


def test_build_postgresql_copy_structure_ddl() -> None:
    ddl = _build_copy_structure_ddl(
        ConnectionType.POSTGRESQL,
        source_schema="core",
        source_table="customers",
        destination_schema="core",
        destination_table="customers_unprocessed",
    )
    assert "CREATE TABLE" in ddl
    assert "LIKE" in ddl
    assert '"core"."customers_unprocessed"' in ddl


def test_build_audit_table_ddl_includes_metadata_columns() -> None:
    ddl = _build_audit_table_ddl(
        ConnectionType.MYSQL,
        destination_schema="core",
        destination_table="migration_conflict_mig_1",
        migration_id="mig_test_2026",
        blueprint_sequence=1,
        target_schema="core",
        target_table="customers",
        primary_key_columns=["id"],
        target_columns=[
            TableColumnSpec(name="id", data_type="bigint", is_nullable=False),
            TableColumnSpec(name="email", data_type="varchar", is_nullable=True),
        ],
    )
    assert "CREATE TABLE `core`.`migration_conflict_mig_1`" in ddl
    assert "`rejected_at`" in ddl
    assert "`logged_at`" in ddl
    assert "`migration_id`" in ddl
    assert "`reject_reason`" in ddl


def test_unsupported_connection_type_raises() -> None:
    with pytest.raises(DdlError):
        _build_copy_structure_ddl(
            ConnectionType.CSV_S3_BUCKET,
            source_schema="core",
            source_table="customers",
            destination_schema="core",
            destination_table="customers_unprocessed",
        )
