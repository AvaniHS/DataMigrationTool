import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import IconButton from "@mui/material/IconButton";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import { ErrorAlertWithRetry } from "@/components/shared/ErrorAlertWithRetry";
import type { ConnectionListItem } from "@/components/connections/types";

type ConnectionListProps = {
  connections: ConnectionListItem[];
  loading: boolean;
  error: string | null;
  onAdd: () => void;
  onEdit: (ref: string) => void;
  onDelete: (ref: string) => void;
  onRetry: () => void;
};

export function ConnectionList({
  connections,
  loading,
  error,
  onAdd,
  onEdit,
  onDelete,
  onRetry,
}: ConnectionListProps) {
  return (
    <Stack spacing={2}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="body2" color="text.secondary">
          Saved connections are assembled into export-ready JSON by the API.
        </Typography>
        <Button variant="contained" onClick={onAdd} disabled={loading}>
          Add connection
        </Button>
      </Box>

      {loading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {error && <ErrorAlertWithRetry message={error} onRetry={onRetry} />}

      {!loading && !error && connections.length === 0 && (
        <Paper variant="outlined" sx={{ p: 4, textAlign: "center" }}>
          <Typography variant="h6" gutterBottom>
            No connections yet
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Add a database or file connector from the catalog. Test connectivity before saving.
          </Typography>
          <Button variant="contained" onClick={onAdd}>
            Add connection
          </Button>
        </Paper>
      )}

      {!loading && !error && connections.length > 0 && (
        <Paper variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Ref</TableCell>
                <TableCell>Connector</TableCell>
                <TableCell>Export type</TableCell>
                <TableCell>Target</TableCell>
                <TableCell>Last tested</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {connections.map((connection) => (
                <TableRow key={connection.ref} hover>
                  <TableCell>{connection.ref}</TableCell>
                  <TableCell>{connection.connector_id}</TableCell>
                  <TableCell>{connection.export_type}</TableCell>
                  <TableCell>{connection.summary}</TableCell>
                  <TableCell>
                    {connection.last_tested_at
                      ? new Date(connection.last_tested_at).toLocaleString()
                      : "—"}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton aria-label={`Edit ${connection.ref}`} onClick={() => onEdit(connection.ref)}>
                      <EditOutlinedIcon />
                    </IconButton>
                    <IconButton
                      aria-label={`Delete ${connection.ref}`}
                      onClick={() => onDelete(connection.ref)}
                    >
                      <DeleteOutlineIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}
    </Stack>
  );
}
