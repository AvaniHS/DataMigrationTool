import { apiFetch } from "./client";

export type SchemaNode = { name: string };
export type TableNode = { name: string; schema: string };
export type ColumnNode = { name: string; data_type: string; is_nullable: boolean };
export type S3FileNode = {
  name: string;
  key: string;
  size_bytes?: number | null;
  last_modified?: string | null;
};

export function listSchemas(connectionRef: string): Promise<SchemaNode[]> {
  return apiFetch<SchemaNode[]>(`/connections/${encodeURIComponent(connectionRef)}/schemas`);
}

export function listTables(connectionRef: string, schema: string): Promise<TableNode[]> {
  return apiFetch<TableNode[]>(
    `/connections/${encodeURIComponent(connectionRef)}/schemas/${encodeURIComponent(schema)}/tables`,
  );
}

export function listColumns(
  connectionRef: string,
  schema: string,
  table: string,
): Promise<ColumnNode[]> {
  return apiFetch<ColumnNode[]>(
    `/connections/${encodeURIComponent(connectionRef)}/schemas/${encodeURIComponent(schema)}/tables/${encodeURIComponent(table)}/columns`,
  );
}

export function listS3Files(connectionRef: string): Promise<S3FileNode[]> {
  return apiFetch<S3FileNode[]>(`/connections/${encodeURIComponent(connectionRef)}/files`);
}
