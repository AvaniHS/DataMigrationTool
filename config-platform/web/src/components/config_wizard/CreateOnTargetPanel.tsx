import { useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import type { ColumnNode } from "@/api/introspection";
import { getApiErrorMessage } from "@/api/errors";
import { copyTableStructure, type CopyStructureMode } from "@/api/tableDdl";
import {
  buildAuditColumnPreview,
  parseQualifiedTableName,
  toTableColumnSpecs,
} from "./tableDdlHelpers";

type CreateOnTargetPanelProps = {
  connectionRef: string;
  mode: CopyStructureMode;
  destinationValue: string;
  onDestinationChange: (value: string) => void;
  migrationId: string;
  blueprintSequence: number;
  sourceSchema?: string;
  sourceTable?: string;
  targetSchema: string;
  targetTable: string;
  primaryKeyColumns: string[];
  targetColumns: ColumnNode[];
  destinationLabel: string;
  helperText?: string;
};

export function CreateOnTargetPanel({
  connectionRef,
  mode,
  destinationValue,
  onDestinationChange,
  migrationId,
  blueprintSequence,
  sourceSchema,
  sourceTable,
  targetSchema,
  targetTable,
  primaryKeyColumns,
  targetColumns,
  destinationLabel,
  helperText,
}: CreateOnTargetPanelProps) {
  const [creating, setCreating] = useState(false);
  const [resultMessage, setResultMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const parsedDestination = parseQualifiedTableName(destinationValue);
  const auditPreview =
    mode === "AUDIT_TABLE" ? buildAuditColumnPreview(targetColumns, primaryKeyColumns) : [];

  const canCreate =
    Boolean(connectionRef) &&
    Boolean(parsedDestination) &&
    (mode === "AUDIT_TABLE"
      ? targetColumns.length > 0 && primaryKeyColumns.length > 0
      : Boolean(sourceSchema && sourceTable));

  const handleCreate = async () => {
    if (!parsedDestination) {
      setError("Enter a destination table as schema.table.");
      return;
    }

    setCreating(true);
    setError(null);
    setResultMessage(null);
    try {
      const response = await copyTableStructure(connectionRef, {
        mode,
        destination_schema: parsedDestination.schema,
        destination_table: parsedDestination.table,
        source_schema: sourceSchema,
        source_table: sourceTable,
        migration_id: migrationId,
        blueprint_sequence: blueprintSequence,
        target_schema: targetSchema,
        target_table: targetTable,
        primary_key_columns: primaryKeyColumns,
        target_columns: mode === "AUDIT_TABLE" ? toTableColumnSpecs(targetColumns) : undefined,
      });
      setResultMessage(response.message);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setCreating(false);
    }
  };

  return (
    <Stack spacing={1}>
      <TextField
        size="small"
        label={destinationLabel}
        value={destinationValue}
        onChange={(event) => onDestinationChange(event.target.value)}
        sx={{ maxWidth: 480 }}
        helperText={helperText}
      />

      {mode === "AUDIT_TABLE" && auditPreview.length > 0 && (
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
            Proposed audit columns
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Column</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Purpose</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {auditPreview.map((column) => (
                <TableRow key={column.name}>
                  <TableCell>{column.name}</TableCell>
                  <TableCell>{column.dataType}</TableCell>
                  <TableCell>{column.purpose}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Box>
      )}

      <Stack direction="row" spacing={1} alignItems="center">
        <Button
          size="small"
          variant="outlined"
          disabled={!canCreate || creating}
          onClick={() => void handleCreate()}
        >
          Create on target
        </Button>
        {creating && <CircularProgress size={18} />}
      </Stack>

      {resultMessage && (
        <Alert severity="success" sx={{ py: 0.5 }}>
          {resultMessage}
        </Alert>
      )}
      {error && (
        <Alert severity="error" sx={{ py: 0.5 }}>
          {error}
        </Alert>
      )}
    </Stack>
  );
}
