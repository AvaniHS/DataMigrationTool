import type { Meta, StoryObj } from "@storybook/react";
import { BlueprintWizardPrototype } from "./BlueprintWizardPrototype";

const meta: Meta<typeof BlueprintWizardPrototype> = {
  title: "Config Wizard/BlueprintWizardPrototype",
  component: BlueprintWizardPrototype,
  parameters: {
    layout: "fullscreen",
  },
};

export default meta;

type Story = StoryObj<typeof BlueprintWizardPrototype>;

export const LayoutTabs: Story = {
  args: {
    initialLayout: "tabs",
    showLayoutToggle: false,
  },
};

export const LayoutSidebar: Story = {
  args: {
    initialLayout: "sidebar",
    showLayoutToggle: false,
  },
};

export const WithLayoutToggle: Story = {
  args: {
    initialLayout: "sidebar",
    showLayoutToggle: true,
  },
};
