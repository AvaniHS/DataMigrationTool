"""Mock schema catalog for dev and tests without live databases."""

from config_platform_api.models.introspection import ColumnNode, SchemaNode, S3FileNode, TableNode

MOCK_SCHEMAS: list[SchemaNode] = [
    SchemaNode(name="crm_db"),
    SchemaNode(name="core"),
    SchemaNode(name="billing"),
]

MOCK_TABLES: dict[str, list[TableNode]] = {
    "crm_db": [
        TableNode(name="customer_master", schema_name="crm_db"),
        TableNode(name="account_status", schema_name="crm_db"),
    ],
    "core": [
        TableNode(name="customers", schema_name="core"),
        TableNode(name="addresses", schema_name="core"),
    ],
    "billing": [
        TableNode(name="billing_details", schema_name="billing"),
    ],
}

MOCK_COLUMNS: dict[tuple[str, str], list[ColumnNode]] = {
    ("crm_db", "customer_master"): [
        ColumnNode(name="id", data_type="bigint", is_nullable=False),
        ColumnNode(name="global_uuid", data_type="char", is_nullable=False),
        ColumnNode(name="company_legal_name", data_type="varchar", is_nullable=False),
        ColumnNode(name="phone_raw", data_type="varchar", is_nullable=True),
        ColumnNode(name="status", data_type="varchar", is_nullable=False),
    ],
    ("core", "customers"): [
        ColumnNode(name="id", data_type="uuid", is_nullable=False),
        ColumnNode(name="company_name", data_type="varchar", is_nullable=False),
        ColumnNode(name="phone", data_type="varchar", is_nullable=True),
        ColumnNode(name="country_iso", data_type="varchar", is_nullable=False),
    ],
}

MOCK_S3_FILES: list[S3FileNode] = [
    S3FileNode(name="geo_address_mapping.csv", key="historical_archives/geo_address_mapping.csv"),
    S3FileNode(name="legacy_customers_2024.csv", key="historical_archives/legacy_customers_2024.csv"),
]


def mock_list_schemas() -> list[SchemaNode]:
    return list(MOCK_SCHEMAS)


def mock_list_tables(schema: str) -> list[TableNode]:
    return list(MOCK_TABLES.get(schema, []))


def mock_list_columns(schema: str, table: str) -> list[ColumnNode]:
    return list(MOCK_COLUMNS.get((schema, table), []))


def mock_list_s3_files() -> list[S3FileNode]:
    return list(MOCK_S3_FILES)
