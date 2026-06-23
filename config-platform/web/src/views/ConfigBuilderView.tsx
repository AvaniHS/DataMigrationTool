import { Link as RouterLink } from "react-router-dom";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { PageHeader } from "@/components/shared/PageHeader";

const MOCK_MIGRATIONS = [
  {
    migrationId: "mig_multi_server_enterprise_2026",
    clientId: "client_global_retail_corp",
    version: "1.0.0",
    blueprintCount: 3,
  },
];

export function ConfigBuilderView() {
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

      <Stack spacing={2}>
        {MOCK_MIGRATIONS.map((migration) => (
          <Paper key={migration.migrationId} variant="outlined" sx={{ p: 2 }}>
            <Stack
              direction={{ xs: "column", sm: "row" }}
              justifyContent="space-between"
              alignItems={{ xs: "flex-start", sm: "center" }}
              spacing={1}
            >
              <Box>
                <Typography variant="h6">{migration.migrationId}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {migration.clientId} · v{migration.version} · {migration.blueprintCount}{" "}
                  blueprints
                </Typography>
              </Box>
              <Button
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
