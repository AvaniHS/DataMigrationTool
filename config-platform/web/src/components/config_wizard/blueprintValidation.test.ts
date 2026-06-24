import { describe, expect, it } from "vitest";
import type { Blueprint } from "@/components/migrations/types";
import {
  syncMappingsFromTargetColumns,
  collectSourceAliases,
} from "./blueprintHelpers";
import {
  validateFiltersStep,
  validateSourcesStep,
  validateTargetStep,
} from "./blueprintValidation";

const connections = [
  { ref: "src_db", connector_id: "mysql", export_type: "MYSQL", category: "database" as const, summary: "", last_tested_at: null, updated_at: "" },
  { ref: "tgt_db", connector_id: "postgresql", export_type: "POSTGRESQL", category: "database" as const, summary: "", last_tested_at: null, updated_at: "" },
];

const emptyBlueprint: Blueprint = {
  sequence_order: 1,
  target: {
    connection_ref: "",
    schema: "",
    table_name: "",
    primary_keys: [],
    on_conflict: "FAIL",
  },
  sources: {
    root_table: {
      connection_ref: "",
      alias: "src",
      schema: "",
      table_name: "",
    },
    joins: [],
  },
  chunking_strategy: { is_enabled: false, chunk_by_column: null, chunk_size: null },
  pre_filters: [],
  post_filters: [],
  derivations: [],
  mappings: [],
};

describe("blueprintValidation", () => {
  it("requires root source fields", () => {
    const result = validateSourcesStep(emptyBlueprint, connections);
    expect(result.valid).toBe(false);
    expect(result.errors.some((item) => item.includes("Root source connection"))).toBe(true);
  });

  it("accepts valid database root source", () => {
    const blueprint: Blueprint = {
      ...emptyBlueprint,
      sources: {
        root_table: {
          connection_ref: "src_db",
          alias: "cm",
          schema: "crm",
          table_name: "customers",
        },
        joins: [],
      },
    };
    expect(validateSourcesStep(blueprint, connections).valid).toBe(true);
  });

  it("requires target primary keys", () => {
    const blueprint: Blueprint = {
      ...emptyBlueprint,
      target: {
        connection_ref: "tgt_db",
        schema: "core",
        table_name: "customers",
        primary_keys: [],
        on_conflict: "UPSERT",
      },
    };
    const result = validateTargetStep(blueprint, connections);
    expect(result.valid).toBe(false);
    expect(result.errors.some((item) => item.includes("primary key"))).toBe(true);
  });

  it("requires chunk fields when chunking enabled", () => {
    const blueprint: Blueprint = {
      ...emptyBlueprint,
      chunking_strategy: { is_enabled: true, chunk_by_column: null, chunk_size: null },
    };
    const result = validateFiltersStep(blueprint);
    expect(result.valid).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });
});

describe("blueprintHelpers", () => {
  it("collects aliases from root and joins", () => {
    const blueprint: Blueprint = {
      ...emptyBlueprint,
      sources: {
        root_table: {
          connection_ref: "src_db",
          alias: "cm",
          schema: "crm",
          table_name: "customers",
        },
        joins: [
          {
            join_type: "LEFT",
            connection_ref: "src_db",
            alias: "addr",
            schema: "crm",
            table_name: "addresses",
            conditions: [],
          },
        ],
      },
    };
    expect(collectSourceAliases(blueprint)).toEqual(["cm", "addr"]);
  });

  it("syncs mappings from target columns while preserving existing rows", () => {
    const blueprint: Blueprint = {
      ...emptyBlueprint,
      mappings: [
        {
          target_column: "id",
          source_type: "DIRECT",
          source_value: "cm.id",
          cast_to: "INT",
          is_nullable: false,
        },
      ],
    };
    const synced = syncMappingsFromTargetColumns(blueprint, [
      { name: "id", data_type: "INT", is_nullable: false },
      { name: "name", data_type: "VARCHAR(255)", is_nullable: true },
    ]);
    expect(synced.mappings).toHaveLength(2);
    expect(synced.mappings[0].source_value).toBe("cm.id");
    expect(synced.mappings[1].target_column).toBe("name");
  });
});
