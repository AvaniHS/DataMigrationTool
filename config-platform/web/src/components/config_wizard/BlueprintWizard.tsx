import { useState } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { BlueprintWizardLayoutSidebar } from "./BlueprintWizardLayoutSidebar";
import { BLUEPRINT_WIZARD_STEPS, SAMPLE_MOCK_MIGRATION, type MockMigration } from "./types";
import { WizardStepMock } from "./WizardStepMock";

type BlueprintWizardProps = {
  migration?: MockMigration;
};

export function BlueprintWizard({ migration = SAMPLE_MOCK_MIGRATION }: BlueprintWizardProps) {
  const [activeStepIndex, setActiveStepIndex] = useState(0);

  const steps = BLUEPRINT_WIZARD_STEPS;
  const activeStep = steps[activeStepIndex];
  const isFirst = activeStepIndex === 0;
  const isLast = activeStepIndex === steps.length - 1;

  return (
    <Box>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6">
          Blueprint {migration.blueprintSequence}: {migration.blueprintName}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {migration.migrationId} · {migration.clientId} v{migration.version}
        </Typography>
      </Box>

      <Stack direction="row" spacing={2} sx={{ alignItems: "stretch" }}>
        <BlueprintWizardLayoutSidebar
          steps={steps}
          activeStepIndex={activeStepIndex}
          onStepChange={setActiveStepIndex}
        />

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
