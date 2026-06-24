import type { Blueprint } from "@/components/migrations/types";
import { apiFetch } from "./client";

export type ValidationIssue = {
  code: string;
  message: string;
  path: string;
  blueprint_sequence: number | null;
};

export type ValidationReport = {
  migration_id: string;
  is_valid: boolean;
  issue_count: number;
  issues: ValidationIssue[];
};

export type MigrationReviewSummary = {
  migration_id: string;
  client_id: string;
  version: string;
  output_format: "SQL";
  blueprint_count: number;
  blueprints: Blueprint[];
};

export function validateMigration(migrationId: string): Promise<ValidationReport> {
  return apiFetch<ValidationReport>(`/migrations/${encodeURIComponent(migrationId)}/validate`, {
    method: "POST",
  });
}
