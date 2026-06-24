import { useCallback, useEffect, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ColumnNode } from "@/api/introspection";
import type { Blueprint } from "@/components/migrations/types";
import type { ConnectionListItem } from "@/components/connections/types";
import { BlueprintWizardLayoutSidebar } from "./BlueprintWizardLayoutSidebar";
import { StepBlueprintReview } from "./StepBlueprintReview";
import { StepFiltersChunking } from "./StepFiltersChunking";
import { StepMappings } from "./StepMappings";
import { StepSourcesJoins } from "./StepSourcesJoins";
import { StepTargetConflict } from "./StepTargetConflict";
import { syncMappingsFromTargetColumns } from "./blueprintHelpers";
import { validateWizardStep } from "./blueprintValidation";
import { BLUEPRINT_WIZARD_STEPS } from "./types";
import { useWizardStepIndex } from "@/hooks/useWizardStepIndex";
import { useLocalDraft } from "@/hooks/useLocalDraft";

type BlueprintWizardProps = {
  migrationId: string;
  clientId: string;
  version: string;
  blueprint: Blueprint;
  connections: ConnectionListItem[];
  onSave: (blueprint: Blueprint) => Promise<void>;
};

export function BlueprintWizard({
  migrationId,
  clientId,
  version,
  blueprint,
  connections,
  onSave,
}: BlueprintWizardProps) {
  const steps = BLUEPRINT_WIZARD_STEPS;
  const draftKey = `wizard-blueprint:${migrationId}:${blueprint.sequence_order}`;
  const [draft, setDraft] = useLocalDraft<Blueprint>(draftKey, blueprint);
  const [activeStepIndex, setActiveStepIndex] = useWizardStepIndex(
    migrationId,
    blueprint.sequence_order,
    steps.length,
  );
  const [targetColumns, setTargetColumns] = useState<ColumnNode[]>([]);
  const [stepErrors, setStepErrors] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const activeStep = steps[activeStepIndex];
  const isFirst = activeStepIndex === 0;
  const isLast = activeStepIndex === steps.length - 1;

  useEffect(() => {
    setDraft(blueprint);
    setStepErrors([]);
    setSaveError(null);
  }, [blueprint, setDraft]);

  const handleBlueprintChange = useCallback((next: Blueprint) => {
    setDraft(next);
    setStepErrors([]);
  }, [setDraft]);

  const handleTargetColumnsLoaded = useCallback(
    (columns: ColumnNode[]) => {
      setTargetColumns(columns);
      if (columns.length === 0) {
        return;
      }
      setDraft((current) => syncMappingsFromTargetColumns(current, columns));
    },
    [setDraft],
  );

  const persistDraft = async (nextDraft: Blueprint) => {
    setSaving(true);
    setSaveError(null);
    try {
      await onSave(nextDraft);
      setDraft(nextDraft);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Unable to save blueprint.");
      throw err;
    } finally {
      setSaving(false);
    }
  };

  const navigateToStep = async (nextIndex: number) => {
    if (nextIndex > activeStepIndex) {
      const validation = validateWizardStep(activeStep.id, draft, connections);
      if (!validation.valid) {
        setStepErrors(validation.errors);
        return;
      }
    }
    setStepErrors([]);
    try {
      await persistDraft(draft);
      setActiveStepIndex(nextIndex);
    } catch {
      // saveError already set
    }
  };

  const blueprintName =
    draft.target.schema && draft.target.table_name
      ? `${draft.target.schema}.${draft.target.table_name}`
      : `Blueprint ${draft.sequence_order}`;

  return (
    <Box>
      <Box sx={{ mb: 1.5 }}>
        <Typography variant="subtitle1" fontWeight={600}>
          Blueprint {draft.sequence_order}: {blueprintName}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {migrationId} · {clientId} v{version}
        </Typography>
      </Box>

      <Stack direction="row" spacing={1.5} sx={{ alignItems: "stretch" }}>
        <BlueprintWizardLayoutSidebar
          steps={steps}
          activeStepIndex={activeStepIndex}
          onStepChange={(index) => {
            void navigateToStep(index);
          }}
        />

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Paper variant="outlined" sx={{ p: 1.5, minHeight: 360 }}>
            {saveError && (
              <Alert severity="error" sx={{ mb: 1 }}>
                {saveError}
              </Alert>
            )}
            {stepErrors.length > 0 && (
              <Alert severity="warning" sx={{ mb: 1 }}>
                <Stack component="ul" sx={{ m: 0, pl: 2 }}>
                  {stepErrors.map((error) => (
                    <Typography key={error} component="li" variant="body2">
                      {error}
                    </Typography>
                  ))}
                </Stack>
              </Alert>
            )}

            {activeStep.id === "sources" && (
              <StepSourcesJoins
                blueprint={draft}
                connections={connections}
                onChange={handleBlueprintChange}
              />
            )}
            {activeStep.id === "target" && (
              <StepTargetConflict
                blueprint={draft}
                connections={connections}
                onChange={handleBlueprintChange}
                onTargetColumnsLoaded={handleTargetColumnsLoaded}
              />
            )}
            {activeStep.id === "mappings" && (
              <StepMappings
                blueprint={draft}
                connections={connections}
                targetColumns={targetColumns}
                onChange={handleBlueprintChange}
              />
            )}
            {activeStep.id === "filters" && (
              <StepFiltersChunking blueprint={draft} onChange={handleBlueprintChange} />
            )}
            {activeStep.id === "review" && <StepBlueprintReview blueprint={draft} />}
          </Paper>

          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mt: 1.5 }}>
            <Button
              size="small"
              disabled={isFirst || saving}
              onClick={() => void navigateToStep(activeStepIndex - 1)}
            >
              Back
            </Button>
            <Stack direction="row" spacing={1} alignItems="center">
              {saving && <CircularProgress size={16} />}
              {!isLast ? (
                <Button
                  size="small"
                  variant="contained"
                  disabled={saving}
                  onClick={() => void navigateToStep(activeStepIndex + 1)}
                >
                  Next
                </Button>
              ) : (
                <Button
                  size="small"
                  variant="contained"
                  disabled={saving}
                  onClick={() => void persistDraft(draft)}
                >
                  Save blueprint
                </Button>
              )}
            </Stack>
          </Stack>
        </Box>
      </Stack>
    </Box>
  );
}
