import { describe, expect, it } from "vitest";
import { blueprintLabel } from "@/components/migrations/types";

describe("blueprintLabel", () => {
  it("uses schema.table when both are set", () => {
    expect(
      blueprintLabel({
        sequence_order: 1,
        target: {
          connection_ref: "",
          schema: "core",
          table_name: "customers",
          primary_keys: [],
          on_conflict: "FAIL",
        },
        sources: { root_table: { connection_ref: "", alias: "src", schema: "", table_name: "" }, joins: [] },
        chunking_strategy: { is_enabled: false, chunk_by_column: null, chunk_size: null },
        pre_filters: [],
        post_filters: [],
        derivations: [],
        mappings: [],
      }),
    ).toBe("core.customers");
  });
});
