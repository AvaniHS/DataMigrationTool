import { useMemo, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import { getApiErrorMessage } from "@/api/errors";
import {
  downloadMigrationExport,
  getMigrationExport,
  type MigrationExportDocument,
} from "@/api/migrationExport";
import {
  validateMigration,
  type ValidationReport,
} from "@/api/migrationValidation";
import { blueprintLabel, type MigrationRecord } from "@/components/migrations/types";

type MigrationReviewPanelProps = {
  migration: MigrationRecord;
};

export function MigrationReviewPanel({ migration }: MigrationReviewPanelProps) {
  const [validationReport, setValidationReport] = useState<ValidationReport | null>(null);
  const [preview, setPreview] = useState<MigrationExportDocument | null>(null);
  const [validating, setValidating] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sortedBlueprints = useMemo(
    () => [...migration.blueprints].sort((left, right) => left.sequence_order - right.sequence_order),
    [migration.blueprints],
  );

  const canDownload = validationReport?.is_valid === true;

  const runValidation = async () => {
    setValidating(true);
    setError(null);
    try {
      setValidationReport(await validateMigration(migration.migration_id));
    } catch (err) {
      setValidationReport(null);
      setError(getApiErrorMessage(err));
    } finally {
      setValidating(false);
    }
  };

  const loadPreview = async () => {
    setLoadingPreview(true);
    setError(null);
    try {
      setPreview(await getMigrationExport(migration.migration_id));
    } catch (err) {
      setPreview(null);
      setError(getApiErrorMessage(err));
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleDownload = async () => {
    if (!canDownload) {
      setError("Run validation and resolve all issues before downloading JSON.");
      return;
    }
    setDownloading(true);
    setError(null);
    try {
      await downloadMigrationExport(migration.migration_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : getApiErrorMessage(err));
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Stack spacing={1.5}>
      <Typography variant="subtitle2">Migration review</Typography>
      <Typography variant="body2" color="text.secondary">
        Review all blueprints, run full validation (L3), then download export JSON when validation passes.
      </Typography>

      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        <Chip size="small" label={`${migration.migration_id}`} />
        <Chip size="small" label={`client: ${migration.client_id}`} />
        <Chip size="small" label={`version: ${migration.version}`} />
        <Chip size="small" label={`${sortedBlueprints.length} blueprint(s)`} />
        {validationReport && (
          <Chip
            size="small"
            color={validationReport.is_valid ? "success" : "warning"}
            label={validationReport.is_valid ? "Validation passed" : "Validation failed"}
          />
        )}
      </Stack>

      <Paper variant="outlined" sx={{ p: 1.5 }}>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Blueprint summary
        </Typography>
        {sortedBlueprints.length === 0 && (
          <Typography variant="body2" color="text.secondary">
            No blueprints configured yet.
          </Typography>
        )}
        <Stack spacing={1}>
          {sortedBlueprints.map((blueprint) => (
            <Box key={blueprint.sequence_order}>
              <Typography variant="body2" fontWeight={600}>
                {blueprint.sequence_order}. {blueprintLabel(blueprint)}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                Target: {blueprint.target.connection_ref || "—"} · conflict {blueprint.target.on_conflict}
                {" · "}
                mappings {blueprint.mappings.length} · joins {blueprint.sources.joins.length}
              </Typography>
            </Box>
          ))}
        </Stack>
      </Paper>

      {error && <Alert severity="warning">{error}</Alert>}

      <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
        <Button
          size="small"
          variant="contained"
          disabled={validating}
          onClick={() => void runValidation()}
        >
          Validate migration
        </Button>
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
          variant="outlined"
          disabled={!canDownload || downloading}
          onClick={() => void handleDownload()}
        >
          Download JSON
        </Button>
        {(validating || loadingPreview || downloading) && <CircularProgress size={18} />}
      </Stack>

      {!canDownload && validationReport && !validationReport.is_valid && (
        <Alert severity="info">
          Download is disabled until validation passes. Fix the issues below and validate again.
        </Alert>
      )}

      {validationReport && validationReport.issues.length > 0 && (
        <Paper variant="outlined" sx={{ p: 1.5 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Validation issues ({validationReport.issue_count})
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Code</TableCell>
                <TableCell>Blueprint</TableCell>
                <TableCell>Path</TableCell>
                <TableCell>Message</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {validationReport.issues.map((issue, index) => (
                <TableRow key={`${issue.code}-${issue.path}-${index}`}>
                  <TableCell>{issue.code}</TableCell>
                  <TableCell>{issue.blueprint_sequence ?? "—"}</TableCell>
                  <TableCell>{issue.path || "—"}</TableCell>
                  <TableCell>{issue.message}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      {preview && (
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.5 }}>
            Export preview · {preview.blueprints.length} blueprint(s) ·{" "}
            {Object.keys(preview.connections).length} connection(s)
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
