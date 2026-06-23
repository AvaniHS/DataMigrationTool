import { useParams } from "react-router-dom";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import { BlueprintWizard } from "@/components/config_wizard/BlueprintWizard";
import { SAMPLE_MOCK_MIGRATION } from "@/mock/sampleData";
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

      <Box>
        <BlueprintWizard
          migration={{
            ...SAMPLE_MOCK_MIGRATION,
            migrationId: migrationId ?? SAMPLE_MOCK_MIGRATION.migrationId,
          }}
        />
      </Box>
    </>
  );
}
