import { Link as RouterLink } from "react-router-dom";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { PageHeader } from "@/components/shared/PageHeader";
import { isMockDataEnabled } from "@/mock/mockProvider";
import { MOCK_MIGRATION_SUMMARIES } from "@/mock/sampleData";

export function ConfigBuilderView() {
  const migrations = isMockDataEnabled() ? MOCK_MIGRATION_SUMMARIES : [];

  return (
    <>
      <PageHeader
        title="Configs"
        description={
          <>
            Migration-level workspace (M0 identity, blueprint list). P0 uses sample data from{" "}
            <code>docs/sampleConfigfile.json</code>.
          </>
        }
      />

      <Stack spacing={1.5}>
        {migrations.length === 0 && (
          <Paper variant="outlined" sx={{ p: 3 }}>
            <Typography variant="body2" color="text.secondary">
              No migrations loaded. Enable mock data with <code>VITE_USE_MOCK_DATA=true</code> or
              wait for P2 migration APIs.
            </Typography>
          </Paper>
        )}

        {migrations.map((migration) => (
          <Paper key={migration.migrationId} variant="outlined" sx={{ p: 1.5 }}>
            <Stack
              direction={{ xs: "column", sm: "row" }}
              justifyContent="space-between"
              alignItems={{ xs: "flex-start", sm: "center" }}
              spacing={1}
            >
              <Box>
                <Typography variant="subtitle1">{migration.migrationId}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {migration.clientId} · v{migration.version} · {migration.blueprintCount}{" "}
                  blueprints
                </Typography>
              </Box>
              <Button
                size="small"
                component={RouterLink}
                to={`/migrations/${migration.migrationId}`}
                variant="contained"
              >
                Open migration
              </Button>
            </Stack>
          </Paper>
        ))}
      </Stack>
    </>
  );
}
