import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Paper from "@mui/material/Paper";
import type { BlueprintWizardStep } from "./types";

type BlueprintWizardLayoutSidebarProps = {
  steps: BlueprintWizardStep[];
  activeStepIndex: number;
  onStepChange: (index: number) => void;
};

export function BlueprintWizardLayoutSidebar({
  steps,
  activeStepIndex,
  onStepChange,
}: BlueprintWizardLayoutSidebarProps) {
  return (
    <Paper variant="outlined" sx={{ width: 220, flexShrink: 0, alignSelf: "stretch" }}>
      <List component="nav" aria-label="Blueprint wizard steps" disablePadding>
        {steps.map((step, index) => (
          <ListItemButton
            key={step.id}
            selected={activeStepIndex === index}
            onClick={() => onStepChange(index)}
          >
            <ListItemText
              primary={step.shortLabel}
              secondary={activeStepIndex === index ? step.label : undefined}
            />
          </ListItemButton>
        ))}
      </List>
    </Paper>
  );
}
