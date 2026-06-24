import { useState } from "react";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import type { CreateMigrationRequest } from "@/components/migrations/types";

type CreateMigrationDialogProps = {
  open: boolean;
  saving?: boolean;
  onClose: () => void;
  onCreate: (body: CreateMigrationRequest) => Promise<void>;
};

export function CreateMigrationDialog({
  open,
  saving = false,
  onClose,
  onCreate,
}: CreateMigrationDialogProps) {
  const [migrationId, setMigrationId] = useState("");
  const [clientId, setClientId] = useState("");
  const [version, setVersion] = useState("1.0.0");
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    setError(null);
    try {
      await onCreate({
        migration_id: migrationId.trim().toLowerCase(),
        client_id: clientId.trim(),
        version: version.trim(),
        output_format: "SQL",
      });
      setMigrationId("");
      setClientId("");
      setVersion("1.0.0");
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create migration.");
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>New migration</DialogTitle>
      <DialogContent>
        <Stack spacing={1.5} sx={{ mt: 0.5 }}>
          <TextField
            size="small"
            label="migration_id"
            helperText="Lowercase slug, e.g. mig_acme_2026"
            value={migrationId}
            disabled={saving}
            onChange={(event) => setMigrationId(event.target.value)}
          />
          <TextField
            size="small"
            label="client_id"
            value={clientId}
            disabled={saving}
            onChange={(event) => setClientId(event.target.value)}
          />
          <TextField
            size="small"
            label="version"
            value={version}
            disabled={saving}
            onChange={(event) => setVersion(event.target.value)}
          />
          {error && (
            <TextField
              size="small"
              value={error}
              disabled
              error
              label="Error"
            />
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button
          variant="contained"
          disabled={saving || !migrationId.trim() || !clientId.trim() || !version.trim()}
          onClick={() => void handleCreate()}
        >
          Create
        </Button>
      </DialogActions>
    </Dialog>
  );
}
