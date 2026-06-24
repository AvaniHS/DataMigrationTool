import { describe, expect, it } from "vitest";
import {
  buildAuditColumnPreview,
  migrationIdShort,
  parseQualifiedTableName,
  proposeAuditTableName,
  proposeUnprocessedTableName,
} from "./tableDdlHelpers";

describe("tableDdlHelpers", () => {
  it("parses qualified table names", () => {
    expect(parseQualifiedTableName("core.customers_unprocessed")).toEqual({
      schema: "core",
      table: "customers_unprocessed",
    });
    expect(parseQualifiedTableName("invalid")).toBeNull();
  });

  it("proposes unprocessed and audit table names", () => {
    expect(proposeUnprocessedTableName("core", "customers")).toBe("core.customers_unprocessed");
    expect(proposeAuditTableName("mig_test_2026", 2, "core")).toBe(
      "core.migration_conflict_mig_test_202_2",
    );
    expect(migrationIdShort("MIG-ABC-123")).toBe("migabc123");
  });

  it("builds audit column preview from target columns", () => {
    const preview = buildAuditColumnPreview(
      [
        { name: "id", data_type: "bigint", is_nullable: false },
        { name: "email", data_type: "varchar", is_nullable: true },
      ],
      ["id"],
    );
    expect(preview.some((column) => column.name === "reject_reason")).toBe(true);
    expect(preview.find((column) => column.name === "id")?.purpose).toContain("PK");
  });
});
