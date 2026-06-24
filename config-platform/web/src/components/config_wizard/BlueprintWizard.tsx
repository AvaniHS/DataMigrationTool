import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { BlueprintWizardLayoutSidebar } from "./BlueprintWizardLayoutSidebar";
import { BLUEPRINT_WIZARD_STEPS } from "./types";
import { WizardStepMock } from "./WizardStepMock";
import { useWizardStepIndex } from "@/hooks/useWizardStepIndex";

type BlueprintWizardProps = {
  migrationId: string;
  clientId: string;
  version: string;
  blueprintSequence: number;
  blueprintName: string;
};

export function BlueprintWizard({
  migrationId,
  clientId,
  version,
  blueprintSequence,
  blueprintName,
}: BlueprintWizardProps) {
  const steps = BLUEPRINT_WIZARD_STEPS;
  const [activeStepIndex, setActiveStepIndex] = useWizardStepIndex(
    migrationId,
    blueprintSequence,
    steps.length,
  );
  const activeStep = steps[activeStepIndex];
  const isFirst = activeStepIndex === 0;
  const isLast = activeStepIndex === steps.length - 1;

  return (
    <Box>
      <Box sx={{ mb: 1.5 }}>
        <Typography variant="subtitle1" fontWeight={600}>
          Blueprint {blueprintSequence}: {blueprintName}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {migrationId} · {clientId} v{version}
        </Typography>
      </Box>

      <Stack direction="row" spacing={1.5} sx={{ alignItems: "stretch" }}>
        <BlueprintWizardLayoutSidebar
          steps={steps}
          activeStepIndex={activeStepIndex}
          onStepChange={setActiveStepIndex}
        />

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <WizardStepMock step={activeStep} />
          <Stack direction="row" justifyContent="space-between" sx={{ mt: 1.5 }}>
            <Button size="small" disabled={isFirst} onClick={() => setActiveStepIndex(activeStepIndex - 1)}>
              Back
            </Button>
            <Button
              size="small"
              variant="contained"
              disabled={isLast}
              onClick={() => setActiveStepIndex(activeStepIndex + 1)}
            >
              Next
            </Button>
          </Stack>
        </Box>
      </Stack>
    </Box>
  );
}
