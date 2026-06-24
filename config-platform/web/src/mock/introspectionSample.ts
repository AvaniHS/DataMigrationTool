import type { ColumnNode, SchemaNode, S3FileNode, TableNode } from "@/api/introspection";

export const MOCK_SCHEMAS: SchemaNode[] = [
  { name: "crm_db" },
  { name: "core" },
  { name: "billing" },
];

export const MOCK_TABLES: Record<string, TableNode[]> = {
  crm_db: [
    { name: "customer_master", schema: "crm_db" },
    { name: "account_status", schema: "crm_db" },
  ],
  core: [
    { name: "customers", schema: "core" },
    { name: "addresses", schema: "core" },
  ],
  billing: [{ name: "billing_details", schema: "billing" }],
};

export const MOCK_COLUMNS: Record<string, ColumnNode[]> = {
  "crm_db/customer_master": [
    { name: "id", data_type: "bigint", is_nullable: false },
    { name: "global_uuid", data_type: "char", is_nullable: false },
    { name: "company_legal_name", data_type: "varchar", is_nullable: false },
    { name: "phone_raw", data_type: "varchar", is_nullable: true },
    { name: "status", data_type: "varchar", is_nullable: false },
  ],
  "core/customers": [
    { name: "id", data_type: "uuid", is_nullable: false },
    { name: "company_name", data_type: "varchar", is_nullable: false },
    { name: "phone", data_type: "varchar", is_nullable: true },
    { name: "country_iso", data_type: "varchar", is_nullable: false },
  ],
};

export const MOCK_S3_FILES: S3FileNode[] = [
  { name: "geo_address_mapping.csv", key: "historical_archives/geo_address_mapping.csv" },
  { name: "legacy_customers_2024.csv", key: "historical_archives/legacy_customers_2024.csv" },
];
