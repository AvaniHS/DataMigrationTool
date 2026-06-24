import { useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { getApiErrorMessage } from "@/api/errors";
import {
  downloadMigrationExport,
  getMigrationExport,
  type MigrationExportDocument,
} from "@/api/migrationExport";

type MigrationExportPanelProps = {
  migrationId: string;
};

export function MigrationExportPanel({ migrationId }: MigrationExportPanelProps) {
  const [preview, setPreview] = useState<MigrationExportDocument | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPreview = async () => {
    setLoadingPreview(true);
    setError(null);
    try {
      setPreview(await getMigrationExport(migrationId));
    } catch (err) {
      setError(getApiErrorMessage(err));
      setPreview(null);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleDownload = async () => {
    setDownloading(true);
    setError(null);
    try {
      await downloadMigrationExport(migrationId);
    } catch (err) {
      setError(err instanceof Error ? err.message : getApiErrorMessage(err));
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Stack spacing={1.5}>
      <Typography variant="subtitle2">Export migration JSON</Typography>
      <Typography variant="body2" color="text.secondary">
        Assembles the migration header, referenced connections, and all blueprints into the shared
        contract shape. Full validate-before-download enforcement ships in P5.
      </Typography>

      {error && <Alert severity="warning">{error}</Alert>}

      <Stack direction="row" spacing={1}>
        <Button
          size="small"
          variant="outlined"
          disabled={loadingPreview}
          onClick={() => void loadPreview()}
        >
          Preview export
        </Button>
        <Button
          size="small"
          variant="contained"
          disabled={downloading}
          onClick={() => void handleDownload()}
        >
          Download JSON
        </Button>
        {(loadingPreview || downloading) && <CircularProgress size={18} />}
      </Stack>

      {preview && (
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
            {preview.blueprints.length} blueprint(s) · {Object.keys(preview.connections).length}{" "}
            connection(s)
          </Typography>
          <Paper
            variant="outlined"
            sx={{
              p: 1.5,
              maxHeight: 320,
              overflow: "auto",
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
              fontSize: 12,
              whiteSpace: "pre-wrap",
            }}
          >
            {JSON.stringify(preview, null, 2)}
          </Paper>
        </Box>
      )}
    </Stack>
  );
}
