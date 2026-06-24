import type { ColumnNode } from "@/api/introspection";
import type { Blueprint, JoinSource } from "@/components/migrations/types";
import type { ConnectionListItem } from "@/components/connections/types";

const FILE_EXPORT_TYPES = new Set(["CSV_S3_BUCKET", "LOCAL_CSV"]);

export function isFileConnectionType(exportType: string): boolean {
  return FILE_EXPORT_TYPES.has(exportType);
}

export function connectionExportType(
  connections: ConnectionListItem[],
  connectionRef: string,
): string | undefined {
  return connections.find((item) => item.ref === connectionRef)?.export_type;
}

export function collectSourceAliases(blueprint: Blueprint): string[] {
  const aliases: string[] = [];
  const rootAlias = blueprint.sources.root_table.alias.trim();
  if (rootAlias) {
    aliases.push(rootAlias);
  }
  for (const join of blueprint.sources.joins) {
    const joinAlias = join.alias.trim();
    if (joinAlias) {
      aliases.push(joinAlias);
    }
  }
  return aliases;
}

export function buildDirectSourceOptions(
  blueprint: Blueprint,
  sourceColumns: Record<string, ColumnNode[]>,
  connections: ConnectionListItem[],
): string[] {
  const options: string[] = [];
  const rootAlias = blueprint.sources.root_table.alias.trim();
  if (rootAlias) {
    const rootKey = sourceKey(
      blueprint.sources.root_table.connection_ref,
      blueprint,
      "root",
      connections,
    );
    for (const column of sourceColumns[rootKey] ?? []) {
      options.push(`${rootAlias}.${column.name}`);
    }
  }
  blueprint.sources.joins.forEach((join, index) => {
    const joinAlias = join.alias.trim();
    if (!joinAlias) {
      return;
    }
    const joinKey = sourceKey(join.connection_ref, blueprint, `join-${index}`, connections);
    for (const column of sourceColumns[joinKey] ?? []) {
      options.push(`${joinAlias}.${column.name}`);
    }
  });
  return options;
}

function sourceKey(
  connectionRef: string,
  blueprint: Blueprint,
  role: string,
  connections: ConnectionListItem[],
): string {
  if (role === "root") {
    const root = blueprint.sources.root_table;
    if (isFileBackedSource(root.connection_ref, connections)) {
      return `${connectionRef}:file:${root.file_name ?? ""}`;
    }
    return `${connectionRef}:table:${root.schema}.${root.table_name}`;
  }
  const joinIndex = Number(role.replace("join-", ""));
  const join = blueprint.sources.joins[joinIndex];
  if (!join) {
    return role;
  }
  if (isFileBackedSource(join.connection_ref, connections)) {
    return `${connectionRef}:file:${join.file_name ?? ""}`;
  }
  return `${connectionRef}:table:${join.schema}.${join.table_name}`;
}

export function isFileBackedSource(
  connectionRef: string,
  connections: ConnectionListItem[],
): boolean {
  const exportType = connectionExportType(connections, connectionRef);
  return exportType ? isFileConnectionType(exportType) : false;
}

export function createEmptyJoin(): JoinSource {
  return {
    join_type: "LEFT",
    connection_ref: "",
    alias: "",
    schema: "",
    table_name: "",
    file_name: null,
    comment: null,
    conditions: [{ left_expression: "", operator: "=", right_expression: "" }],
  };
}

export function syncMappingsFromTargetColumns(
  blueprint: Blueprint,
  targetColumns: ColumnNode[],
): Blueprint {
  if (targetColumns.length === 0) {
    return blueprint;
  }
  const existingByColumn = new Map(
    blueprint.mappings.map((mapping) => [mapping.target_column, mapping]),
  );
  const mappings = targetColumns.map((column) => {
    const existing = existingByColumn.get(column.name);
    if (existing) {
      return existing;
    }
    return {
      target_column: column.name,
      source_type: "DIRECT",
      source_value: "",
      cast_to: column.data_type,
      is_nullable: column.is_nullable,
    };
  });
  return { ...blueprint, mappings };
}

export const ON_CONFLICT_OPTIONS = [
  "FAIL",
  "IGNORE",
  "UPSERT",
  "IGNORE_AND_LOG",
  "IGNORE_AND_INSERT_UNPROCESSED",
] as const;

export const SOURCE_TYPE_OPTIONS = ["DIRECT", "CONSTANT", "DERIVED", "EXPRESSION"] as const;

export const JOIN_TYPE_OPTIONS = ["INNER", "LEFT", "RIGHT", "FULL"] as const;
