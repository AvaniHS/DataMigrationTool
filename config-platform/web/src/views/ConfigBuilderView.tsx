import { useState } from "react";
import { Link as RouterLink } from "react-router-dom";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { getApiErrorMessage } from "@/api/errors";
import { CreateMigrationDialog } from "@/components/migrations/CreateMigrationDialog";
import { PageHeader } from "@/components/shared/PageHeader";
import { ErrorAlertWithRetry } from "@/components/shared/ErrorAlertWithRetry";
import { useMigrations } from "@/hooks/useMigrations";

export function ConfigBuilderView() {
  const { migrations, loading, error, refresh, create, remove } = useMigrations();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [deletingMigrationId, setDeletingMigrationId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const handleCreate = async (body: Parameters<typeof create>[0]) => {
    setCreating(true);
    setActionError(null);
    try {
      await create(body);
    } catch (err) {
      setActionError(getApiErrorMessage(err));
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (migrationId: string) => {
    if (!window.confirm(`Delete migration "${migrationId}" and all its blueprints?`)) {
      return;
    }
    setDeletingMigrationId(migrationId);
    setActionError(null);
    try {
      await remove(migrationId);
    } catch (err) {
      setActionError(getApiErrorMessage(err));
    } finally {
      setDeletingMigrationId(null);
    }
  };

  return (
    <>
      <PageHeader
        title="Configs"
        description="Migration-level workspace: identity (M0), blueprint list (M2), and per-blueprint wizard."
      />

      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
        <Typography variant="body2" color="text.secondary">
          Draft migrations are stored by the config API.
        </Typography>
        <Button variant="contained" onClick={() => setDialogOpen(true)} disabled={loading}>
          New migration
        </Button>
      </Stack>

      {loading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {error && <ErrorAlertWithRetry message={error} onRetry={() => void refresh()} />}
      {actionError && <ErrorAlertWithRetry message={actionError} onRetry={() => setActionError(null)} />}

      {!loading && !error && migrations.length === 0 && (
        <Paper variant="outlined" sx={{ p: 3 }}>
          <Typography variant="body2" color="text.secondary">
            No migrations yet. Create one to start configuring blueprints.
          </Typography>
        </Paper>
      )}

      <Stack spacing={1.5}>
        {migrations.map((migration) => (
          <Paper key={migration.migration_id} variant="outlined" sx={{ p: 1.5 }}>
            <Stack
              direction={{ xs: "column", sm: "row" }}
              justifyContent="space-between"
              alignItems={{ xs: "flex-start", sm: "center" }}
              spacing={1}
            >
              <Box>
                <Typography variant="subtitle1">{migration.migration_id}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {migration.client_id} · v{migration.version} · {migration.blueprint_count}{" "}
                  blueprints
                </Typography>
              </Box>
              <Stack direction="row" spacing={1}>
                <Button
                  size="small"
                  component={RouterLink}
                  to={`/migrations/${migration.migration_id}`}
                  variant="contained"
                >
                  Open migration
                </Button>
                <Button
                  size="small"
                  color="error"
                  variant="outlined"
                  disabled={deletingMigrationId === migration.migration_id}
                  onClick={() => void handleDelete(migration.migration_id)}
                >
                  {deletingMigrationId === migration.migration_id ? "Deleting…" : "Delete"}
                </Button>
              </Stack>
            </Stack>
          </Paper>
        ))}
      </Stack>

      <CreateMigrationDialog
        open={dialogOpen}
        saving={creating}
        onClose={() => setDialogOpen(false)}
        onCreate={handleCreate}
      />
    </>
  );
}
