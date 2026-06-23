import { useState } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";
import { BlueprintWizardLayoutSidebar } from "./BlueprintWizardLayoutSidebar";
import { BlueprintWizardLayoutTabs } from "./BlueprintWizardLayoutTabs";
import {
  BLUEPRINT_WIZARD_STEPS,
  SAMPLE_MOCK_MIGRATION,
  type BlueprintLayoutMode,
  type MockMigration,
} from "./types";
import { WizardStepMock } from "./WizardStepMock";

type BlueprintWizardPrototypeProps = {
  migration?: MockMigration;
  initialLayout?: BlueprintLayoutMode;
  showLayoutToggle?: boolean;
};

export function BlueprintWizardPrototype({
  migration = SAMPLE_MOCK_MIGRATION,
  initialLayout = "sidebar",
  showLayoutToggle = true,
}: BlueprintWizardPrototypeProps) {
  const [layoutMode, setLayoutMode] = useState<BlueprintLayoutMode>(initialLayout);
  const [activeStepIndex, setActiveStepIndex] = useState(0);

  const steps = BLUEPRINT_WIZARD_STEPS;
  const activeStep = steps[activeStepIndex];
  const isFirst = activeStepIndex === 0;
  const isLast = activeStepIndex === steps.length - 1;

  return (
    <Box>
      <Stack
        direction={{ xs: "column", sm: "row" }}
        justifyContent="space-between"
        alignItems={{ xs: "flex-start", sm: "center" }}
        spacing={1}
        sx={{ mb: 2 }}
      >
        <Box>
          <Typography variant="h6">
            Blueprint {migration.blueprintSequence}: {migration.blueprintName}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {migration.migrationId} · {migration.clientId} v{migration.version}
          </Typography>
        </Box>
        <Stack direction="row" spacing={1} alignItems="center">
          <Chip label="P0 prototype" size="small" color="info" variant="outlined" />
          {showLayoutToggle && (
            <ToggleButtonGroup
              size="small"
              exclusive
              value={layoutMode}
              onChange={(_, value: BlueprintLayoutMode | null) => {
                if (value) {
                  setLayoutMode(value);
                }
              }}
              aria-label="Blueprint layout mode"
            >
              <ToggleButton value="tabs">Layout A — Tabs</ToggleButton>
              <ToggleButton value="sidebar">Layout B — Sidebar</ToggleButton>
            </ToggleButtonGroup>
          )}
        </Stack>
      </Stack>

      {layoutMode === "tabs" && (
        <BlueprintWizardLayoutTabs
          steps={steps}
          activeStepIndex={activeStepIndex}
          onStepChange={setActiveStepIndex}
        />
      )}

      <Stack
        direction="row"
        spacing={2}
        sx={{ mt: layoutMode === "tabs" ? 2 : 0, alignItems: "stretch" }}
      >
        {layoutMode === "sidebar" && (
          <BlueprintWizardLayoutSidebar
            steps={steps}
            activeStepIndex={activeStepIndex}
            onStepChange={setActiveStepIndex}
          />
        )}

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <WizardStepMock step={activeStep} />
          <Stack direction="row" justifyContent="space-between" sx={{ mt: 2 }}>
            <Button disabled={isFirst} onClick={() => setActiveStepIndex((i) => i - 1)}>
              Back
            </Button>
            <Button
              variant="contained"
              disabled={isLast}
              onClick={() => setActiveStepIndex((i) => i + 1)}
            >
              Next
            </Button>
          </Stack>
        </Box>
      </Stack>
    </Box>
  );
}
