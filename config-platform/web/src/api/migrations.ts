import { apiFetch } from "./client";
import type {
  CreateMigrationRequest,
  MigrationListItem,
  MigrationRecord,
  UpdateMigrationRequest,
} from "@/components/migrations/types";

export function listMigrations(): Promise<MigrationListItem[]> {
  return apiFetch<MigrationListItem[]>("/migrations");
}

export function getMigration(migrationId: string): Promise<MigrationRecord> {
  return apiFetch<MigrationRecord>(`/migrations/${encodeURIComponent(migrationId)}`);
}

export function createMigration(body: CreateMigrationRequest): Promise<MigrationRecord> {
  return apiFetch<MigrationRecord>("/migrations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function updateMigration(
  migrationId: string,
  body: UpdateMigrationRequest,
): Promise<MigrationRecord> {
  return apiFetch<MigrationRecord>(`/migrations/${encodeURIComponent(migrationId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function deleteMigration(migrationId: string): Promise<void> {
  return apiFetch<void>(`/migrations/${encodeURIComponent(migrationId)}`, {
    method: "DELETE",
  });
}

export function addBlueprint(migrationId: string): Promise<MigrationRecord> {
  return apiFetch<MigrationRecord>(`/migrations/${encodeURIComponent(migrationId)}/blueprints`, {
    method: "POST",
  });
}

export function deleteBlueprint(migrationId: string, sequenceOrder: number): Promise<MigrationRecord> {
  return apiFetch<MigrationRecord>(
    `/migrations/${encodeURIComponent(migrationId)}/blueprints/${sequenceOrder}`,
    { method: "DELETE" },
  );
}

export function duplicateBlueprint(
  migrationId: string,
  sequenceOrder: number,
): Promise<MigrationRecord> {
  return apiFetch<MigrationRecord>(
    `/migrations/${encodeURIComponent(migrationId)}/blueprints/${sequenceOrder}/duplicate`,
    { method: "POST" },
  );
}

export function reorderBlueprints(
  migrationId: string,
  sequenceOrders: number[],
): Promise<MigrationRecord> {
  return apiFetch<MigrationRecord>(
    `/migrations/${encodeURIComponent(migrationId)}/blueprints/reorder`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sequence_orders: sequenceOrders }),
    },
  );
}
