export type MigrationListItem = {
  migration_id: string;
  client_id: string;
  version: string;
  output_format: "SQL";
  blueprint_count: number;
  updated_at: string;
};

export type BlueprintTarget = {
  connection_ref: string;
  schema: string;
  table_name: string;
  primary_keys: string[];
  on_conflict: string;
  unprocessed_table?: string | null;
};

export type RootTableSource = {
  connection_ref: string;
  alias: string;
  schema: string;
  table_name: string;
  file_name?: string | null;
  comment?: string | null;
};

export type JoinSource = {
  join_type: "INNER" | "LEFT" | "RIGHT" | "FULL";
  connection_ref: string;
  alias: string;
  schema: string;
  table_name: string;
  file_name?: string | null;
  comment?: string | null;
  conditions: Array<{
    left_expression: string;
    operator: string;
    right_expression: string;
  }>;
};

export type Blueprint = {
  sequence_order: number;
  target: BlueprintTarget;
  sources: {
    root_table: RootTableSource;
    joins: JoinSource[];
  };
  chunking_strategy: {
    is_enabled: boolean;
    chunk_by_column: string | null;
    chunk_size: number | null;
  };
  pre_filters: string[];
  post_filters: string[];
  derivations: Array<{ variable_name: string; expression: string }>;
  mappings: Array<{
    target_column: string;
    source_type: string;
    source_value: string;
    cast_to: string;
    is_nullable: boolean;
  }>;
};

export type MigrationRecord = {
  migration_id: string;
  client_id: string;
  version: string;
  output_format: "SQL";
  blueprints: Blueprint[];
  created_at: string;
  updated_at: string;
};

export type CreateMigrationRequest = {
  migration_id: string;
  client_id: string;
  version: string;
  output_format?: "SQL";
};

export type UpdateMigrationRequest = {
  client_id: string;
  version: string;
  blueprints: Blueprint[];
};

export type MigrationHeaderValues = {
  migration_id: string;
  client_id: string;
  version: string;
};

export function blueprintLabel(blueprint: Blueprint): string {
  const target = blueprint.target;
  if (target.schema && target.table_name) {
    return `${target.schema}.${target.table_name}`;
  }
  if (target.table_name) {
    return target.table_name;
  }
  return `Blueprint ${blueprint.sequence_order}`;
}
