import type { ColumnNode } from "@/api/introspection";

export type QualifiedTableName = {
  schema: string;
  table: string;
};

export function parseQualifiedTableName(qualified: string): QualifiedTableName | null {
  const trimmed = qualified.trim();
  const dotIndex = trimmed.lastIndexOf(".");
  if (dotIndex <= 0 || dotIndex === trimmed.length - 1) {
    return null;
  }
  return {
    schema: trimmed.slice(0, dotIndex),
    table: trimmed.slice(dotIndex + 1),
  };
}

export function formatQualifiedTableName(schema: string, table: string): string {
  return `${schema}.${table}`;
}

export function migrationIdShort(migrationId: string): string {
  const normalized = migrationId.trim().toLowerCase().replace(/[^a-z0-9_]/g, "");
  return normalized.slice(0, 12) || "migration";
}

export function proposeAuditTableName(
  migrationId: string,
  blueprintSequence: number,
  targetSchema: string,
): string {
  return formatQualifiedTableName(
    targetSchema,
    `migration_conflict_${migrationIdShort(migrationId)}_${blueprintSequence}`,
  );
}

export function proposeUnprocessedTableName(targetSchema: string, targetTable: string): string {
  const safeTable = targetTable.trim() || "target";
  return formatQualifiedTableName(targetSchema, `${safeTable}_unprocessed`);
}

export type AuditColumnPreview = {
  name: string;
  dataType: string;
  purpose: string;
};

export function buildAuditColumnPreview(
  targetColumns: ColumnNode[],
  primaryKeyColumns: string[],
): AuditColumnPreview[] {
  const projectionColumns = targetColumns.map((column) => ({
    name: column.name,
    dataType: column.data_type,
    purpose: primaryKeyColumns.includes(column.name) ? "Conflict row identity (PK)" : "Projected target column",
  }));

  return [
    ...projectionColumns,
    { name: "rejected_at", dataType: "timestamp", purpose: "Engine conflict capture timestamp" },
    { name: "logged_at", dataType: "timestamp", purpose: "Audit timestamp (§12.4)" },
    { name: "migration_id", dataType: "varchar(128)", purpose: "Migration identity" },
    { name: "blueprint_sequence", dataType: "int", purpose: "Blueprint sequence" },
    { name: "target_schema", dataType: "varchar(128)", purpose: "Target schema" },
    { name: "target_table", dataType: "varchar(128)", purpose: "Target table" },
    { name: "source_snapshot", dataType: "text", purpose: "Optional mapped source values" },
    { name: "reject_reason", dataType: "varchar(64)", purpose: "e.g. DUPLICATE_KEY" },
    { name: "raw_row", dataType: "text", purpose: "Optional projected row JSON" },
  ];
}

export function toTableColumnSpecs(columns: ColumnNode[]) {
  return columns.map((column) => ({
    name: column.name,
    data_type: column.data_type,
    is_nullable: column.is_nullable,
  }));
}
