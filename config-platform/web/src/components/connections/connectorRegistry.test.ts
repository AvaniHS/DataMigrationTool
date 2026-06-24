import { describe, expect, it } from "vitest";
import {
  catalogByCategory,
  CONNECTOR_FORM_REGISTRY,
  findCatalogItem,
  getConnectorFormComponent,
} from "@/components/connections/connectorRegistry";
import type { ConnectorCatalogItem } from "@/components/connections/types";

const sampleCatalog: ConnectorCatalogItem[] = [
  {
    connector_id: "mysql",
    label: "MySQL",
    description: "MySQL database",
    category: "database",
    export_type: "MYSQL",
    auth_methods: [{ id: "password", label: "Password", delivery_phase: "P1.2" }],
  },
  {
    connector_id: "csv_s3_bucket",
    label: "CSV on S3",
    description: "S3 bucket",
    category: "file",
    export_type: "CSV_S3_BUCKET",
    auth_methods: [{ id: "access_key", label: "Access key", delivery_phase: "P1.2" }],
  },
  {
    connector_id: "local_csv",
    label: "Local CSV",
    description: "Local file",
    category: "file",
    export_type: "LOCAL_CSV",
    auth_methods: [{ id: "local_path", label: "Local path", delivery_phase: "P1.5" }],
  },
];

describe("connectorRegistry", () => {
  it("registers all six Phase 1 connector forms", () => {
    expect(Object.keys(CONNECTOR_FORM_REGISTRY).sort()).toEqual([
      "azure_sql_database",
      "csv_s3_bucket",
      "local_csv",
      "mssql_onprem",
      "mysql",
      "postgresql",
    ]);
  });

  it("returns a form component for known connector ids", () => {
    expect(getConnectorFormComponent("mysql")).not.toBeNull();
    expect(getConnectorFormComponent("unknown")).toBeNull();
  });

  it("filters catalog items by category", () => {
    expect(catalogByCategory(sampleCatalog, "database").map((item) => item.connector_id)).toEqual([
      "mysql",
    ]);
    expect(catalogByCategory(sampleCatalog, "file").map((item) => item.connector_id)).toEqual([
      "csv_s3_bucket",
      "local_csv",
    ]);
  });

  it("finds catalog items by connector id", () => {
    expect(findCatalogItem(sampleCatalog, "mysql")?.label).toBe("MySQL");
    expect(findCatalogItem(sampleCatalog, "missing")).toBeUndefined();
  });
});
