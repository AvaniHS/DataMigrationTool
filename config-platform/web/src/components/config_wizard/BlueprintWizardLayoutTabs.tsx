import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import type { BlueprintWizardStep } from "./types";

type BlueprintWizardLayoutTabsProps = {
  steps: BlueprintWizardStep[];
  activeStepIndex: number;
  onStepChange: (index: number) => void;
};

export function BlueprintWizardLayoutTabs({
  steps,
  activeStepIndex,
  onStepChange,
}: BlueprintWizardLayoutTabsProps) {
  return (
    <Tabs
      value={activeStepIndex}
      onChange={(_, value: number) => onStepChange(value)}
      variant="scrollable"
      scrollButtons="auto"
      aria-label="Blueprint wizard steps"
    >
      {steps.map((step, index) => (
        <Tab key={step.id} label={`${index + 1} ${step.shortLabel}`} />
      ))}
    </Tabs>
  );
}
