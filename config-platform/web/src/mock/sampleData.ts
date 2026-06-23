export type MockMigrationSummary = {
  migrationId: string;
  clientId: string;
  version: string;
  blueprintCount: number;
};

export type MockMigration = {
  migrationId: string;
  clientId: string;
  version: string;
  blueprintName: string;
  blueprintSequence: number;
};

/** Contract-aligned sample data from docs/sampleConfigfile.json */
export const MOCK_MIGRATION_SUMMARIES: MockMigrationSummary[] = [
  {
    migrationId: "mig_multi_server_enterprise_2026",
    clientId: "client_global_retail_corp",
    version: "1.0.0",
    blueprintCount: 3,
  },
];

export const SAMPLE_MOCK_MIGRATION: MockMigration = {
  migrationId: "mig_multi_server_enterprise_2026",
  clientId: "client_global_retail_corp",
  version: "1.0.0",
  blueprintName: "customers",
  blueprintSequence: 1,
};
