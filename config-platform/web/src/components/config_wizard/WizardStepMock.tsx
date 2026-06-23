import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import type { BlueprintWizardStep } from "./types";

type WizardStepMockProps = {
  step: BlueprintWizardStep;
};

export function WizardStepMock({ step }: WizardStepMockProps) {
  return (
    <Paper variant="outlined" sx={{ p: 3, minHeight: 280 }}>
      <Typography variant="h6" gutterBottom>
        {step.label}
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        {step.description}
      </Typography>
      <Box
        sx={{
          mt: 2,
          p: 2,
          bgcolor: "action.hover",
          borderRadius: 1,
          fontFamily: "monospace",
          fontSize: 13,
        }}
      >
        {step.id === "sources" && (
          <>
            Left: SchemaTree (connection switcher)
            <br />
            Right: Source graph — root_table + joins[]
          </>
        )}
        {step.id === "target" && (
          <>
            Target connection, schema.table, primary_keys[]
            <br />
            on_conflict: FAIL | IGNORE | UPSERT | IGNORE_AND_LOG | IGNORE_AND_INSERT_UNPROCESSED
          </>
        )}
        {step.id === "mappings" && (
          <>
            Derivations drawer + MUI X Data Grid
            <br />
            Rows: source_type, source_value, cast_to, is_nullable
          </>
        )}
        {step.id === "filters" && (
          <>
            pre_filters[] / post_filters[]
            <br />
            chunking_strategy.is_enabled, chunk_by_column, chunk_size
          </>
        )}
        {step.id === "review" && <>Read-only blueprint summary and validation hints.</>}
      </Box>
    </Paper>
  );
}
