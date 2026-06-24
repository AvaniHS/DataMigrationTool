import type { Meta, StoryObj } from "@storybook/react";
import { BlueprintWizard } from "./BlueprintWizard";

const meta: Meta<typeof BlueprintWizard> = {
  title: "Config Wizard/BlueprintWizard",
  component: BlueprintWizard,
  parameters: {
    layout: "fullscreen",
  },
};

export default meta;

type Story = StoryObj<typeof BlueprintWizard>;

const sampleBlueprint = {
  sequence_order: 1,
  target: {
    connection_ref: "target_production_system",
    schema: "core",
    table_name: "customers",
    primary_keys: ["id"],
    on_conflict: "UPSERT",
  },
  sources: {
    root_table: {
      connection_ref: "client_crm_mysql",
      alias: "cm",
      schema: "crm_db",
      table_name: "customer_master",
    },
    joins: [],
  },
  chunking_strategy: { is_enabled: false, chunk_by_column: null, chunk_size: null },
  pre_filters: [],
  post_filters: [],
  derivations: [],
  mappings: [],
};

const sampleConnections = [
  {
    ref: "client_crm_mysql",
    connector_id: "mysql",
    export_type: "MYSQL",
    category: "database" as const,
    summary: "",
    last_tested_at: null,
    updated_at: "",
  },
  {
    ref: "target_production_system",
    connector_id: "postgresql",
    export_type: "POSTGRESQL",
    category: "database" as const,
    summary: "",
    last_tested_at: null,
    updated_at: "",
  },
];

export const Default: Story = {
  args: {
    migrationId: "mig_multi_server_enterprise_2026",
    clientId: "client_global_retail_corp",
    version: "1.0.0",
    blueprint: sampleBlueprint,
    connections: sampleConnections,
    onSave: async () => undefined,
  },
};
