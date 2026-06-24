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

export const Default: Story = {
  args: {
    migrationId: "mig_multi_server_enterprise_2026",
    clientId: "client_global_retail_corp",
    version: "1.0.0",
    blueprintSequence: 1,
    blueprintName: "core.customers",
  },
};
