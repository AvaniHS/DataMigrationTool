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

export const Default: Story = {};
