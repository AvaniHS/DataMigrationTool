import { apiFetch } from "./client";

export type CopyStructureMode = "COPY_FROM_TABLE" | "AUDIT_TABLE";

export type TableColumnSpec = {
  name: string;
  data_type: string;
  is_nullable: boolean;
};

export type CopyStructureRequest = {
  mode: CopyStructureMode;
  destination_schema: string;
  destination_table: string;
  source_schema?: string;
  source_table?: string;
  migration_id?: string;
  blueprint_sequence?: number;
  target_schema?: string;
  target_table?: string;
  primary_key_columns?: string[];
  target_columns?: TableColumnSpec[];
};

export type CopyStructureResponse = {
  connection_ref: string;
  mode: CopyStructureMode;
  qualified_name: string;
  created: boolean;
  skipped_existing: boolean;
  message: string;
};

export function copyTableStructure(
  connectionRef: string,
  request: CopyStructureRequest,
): Promise<CopyStructureResponse> {
  return apiFetch<CopyStructureResponse>(
    `/connections/${encodeURIComponent(connectionRef)}/tables/copy-structure`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    },
  );
}
