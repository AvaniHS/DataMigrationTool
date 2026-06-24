import type { Blueprint } from "@/components/migrations/types";
import { apiBaseUrl, apiFetch } from "./client";

export type MigrationExportDocument = {
  migration_id: string;
  client_id: string;
  version: string;
  output_format: "SQL";
  connections: Record<string, Record<string, unknown>>;
  blueprints: Blueprint[];
};

export function getMigrationExport(migrationId: string): Promise<MigrationExportDocument> {
  return apiFetch<MigrationExportDocument>(`/migrations/${encodeURIComponent(migrationId)}/export`);
}

export async function downloadMigrationExport(migrationId: string): Promise<void> {
  const url = `${apiBaseUrl}/migrations/${encodeURIComponent(migrationId)}/export?download=true`;
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    let message = `Export download failed: ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        message = body.detail;
      }
    } catch {
      // Use default message.
    }
    throw new Error(message);
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = `${migrationId}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}
