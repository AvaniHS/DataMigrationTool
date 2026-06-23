import { useParams } from "react-router-dom";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import { BlueprintWizardPrototype } from "@/components/config_wizard/BlueprintWizardPrototype";
import { SAMPLE_MOCK_MIGRATION } from "@/components/config_wizard/types";
import { PageHeader } from "@/components/shared/PageHeader";

export function MigrationDetailView() {
  const { migrationId } = useParams<{ migrationId: string }>();

  return (
    <>
      <PageHeader title="Migration workspace">
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          <Chip label={`migration_id: ${migrationId ?? "—"}`} size="small" />
          <Chip label="output_format: SQL" size="small" variant="outlined" />
          <Chip label="compile dialect: MySQL" size="small" variant="outlined" />
        </Stack>
      </PageHeader>

      <Alert severity="info" sx={{ mb: 3 }}>
        Compare <strong>Layout A (tabs)</strong> vs <strong>Layout B (sidebar)</strong> using the
        toggle below. Pick a winner before P3 (OQ-5).
      </Alert>

      <Box>
        <BlueprintWizardPrototype
          migration={{
            ...SAMPLE_MOCK_MIGRATION,
            migrationId: migrationId ?? SAMPLE_MOCK_MIGRATION.migrationId,
          }}
        />
      </Box>
    </>
  );
}
