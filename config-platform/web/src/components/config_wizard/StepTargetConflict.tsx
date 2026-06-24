import { useCallback, useEffect, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Checkbox from "@mui/material/Checkbox";
import CircularProgress from "@mui/material/CircularProgress";
import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormGroup from "@mui/material/FormGroup";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { listColumns, listSchemas, listTables, type ColumnNode } from "@/api/introspection";
import { getApiErrorMessage } from "@/api/errors";
import type { Blueprint } from "@/components/migrations/types";
import type { ConnectionListItem } from "@/components/connections/types";
import { ON_CONFLICT_OPTIONS } from "./blueprintHelpers";
import { CreateOnTargetPanel } from "./CreateOnTargetPanel";
import { proposeAuditTableName, proposeUnprocessedTableName } from "./tableDdlHelpers";

type StepTargetConflictProps = {
  migrationId: string;
  blueprint: Blueprint;
  connections: ConnectionListItem[];
  onChange: (blueprint: Blueprint) => void;
  onTargetColumnsLoaded: (columns: ColumnNode[]) => void;
};

export function StepTargetConflict({
  migrationId,
  blueprint,
  connections,
  onChange,
  onTargetColumnsLoaded,
}: StepTargetConflictProps) {
  const target = blueprint.target;
  const [schemas, setSchemas] = useState<string[]>([]);
  const [tables, setTables] = useState<string[]>([]);
  const [columns, setColumns] = useState<ColumnNode[]>([]);
  const [loadingSchemas, setLoadingSchemas] = useState(false);
  const [loadingTables, setLoadingTables] = useState(false);
  const [loadingColumns, setLoadingColumns] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const databaseConnections = connections.filter((item) => item.category === "database");

  const updateTarget = (patch: Partial<Blueprint["target"]>) => {
    onChange({
      ...blueprint,
      target: { ...target, ...patch },
    });
  };

  const loadSchemas = useCallback(async (connectionRef: string) => {
    if (!connectionRef) {
      setSchemas([]);
      return;
    }
    setLoadingSchemas(true);
    setError(null);
    try {
      const nodes = await listSchemas(connectionRef);
      setSchemas(nodes.map((item) => item.name));
    } catch (err) {
      setError(getApiErrorMessage(err));
      setSchemas([]);
    } finally {
      setLoadingSchemas(false);
    }
  }, []);

  const loadTables = useCallback(async (connectionRef: string, schema: string) => {
    if (!connectionRef || !schema) {
      setTables([]);
      return;
    }
    setLoadingTables(true);
    setError(null);
    try {
      const nodes = await listTables(connectionRef, schema);
      setTables(nodes.map((item) => item.name));
    } catch (err) {
      setError(getApiErrorMessage(err));
      setTables([]);
    } finally {
      setLoadingTables(false);
    }
  }, []);

  const loadTargetColumns = useCallback(
    async (connectionRef: string, schema: string, table: string) => {
      if (!connectionRef || !schema || !table) {
        setColumns([]);
        onTargetColumnsLoaded([]);
        return;
      }
      setLoadingColumns(true);
      setError(null);
      try {
        const nodes = await listColumns(connectionRef, schema, table);
        setColumns(nodes);
        onTargetColumnsLoaded(nodes);
      } catch (err) {
        setError(getApiErrorMessage(err));
        setColumns([]);
        onTargetColumnsLoaded([]);
      } finally {
        setLoadingColumns(false);
      }
    },
    [onTargetColumnsLoaded],
  );

  useEffect(() => {
    void loadSchemas(target.connection_ref);
  }, [loadSchemas, target.connection_ref]);

  useEffect(() => {
    void loadTables(target.connection_ref, target.schema);
  }, [loadTables, target.connection_ref, target.schema]);

  useEffect(() => {
    void loadTargetColumns(target.connection_ref, target.schema, target.table_name);
  }, [loadTargetColumns, target.connection_ref, target.schema, target.table_name]);

  useEffect(() => {
    if (target.on_conflict !== "IGNORE_AND_INSERT_UNPROCESSED") {
      return;
    }
    if (target.unprocessed_table?.trim() || !target.schema || !target.table_name) {
      return;
    }
    updateTarget({ unprocessed_table: proposeUnprocessedTableName(target.schema, target.table_name) });
  }, [target.on_conflict, target.schema, target.table_name, target.unprocessed_table]);

  useEffect(() => {
    if (target.on_conflict !== "IGNORE_AND_LOG") {
      return;
    }
    if (target.audit_table?.trim() || !target.schema) {
      return;
    }
    updateTarget({
      audit_table: proposeAuditTableName(migrationId, blueprint.sequence_order, target.schema),
    });
  }, [target.on_conflict, target.schema, target.audit_table, migrationId, blueprint.sequence_order]);

  const togglePrimaryKey = (columnName: string) => {
    const selected = new Set(target.primary_keys);
    if (selected.has(columnName)) {
      selected.delete(columnName);
    } else {
      selected.add(columnName);
    }
    updateTarget({ primary_keys: Array.from(selected) });
  };

  return (
    <Stack spacing={1.5}>
      {error && <Alert severity="warning">{error}</Alert>}

      <Stack direction={{ xs: "column", md: "row" }} spacing={1}>
        <FormControl size="small" sx={{ minWidth: 220 }}>
          <InputLabel id="target-connection-label">Target connection</InputLabel>
          <Select
            labelId="target-connection-label"
            label="Target connection"
            value={target.connection_ref}
            onChange={(event) =>
              updateTarget({
                connection_ref: event.target.value,
                schema: "",
                table_name: "",
                primary_keys: [],
              })
            }
          >
            {databaseConnections.map((connection) => (
              <MenuItem key={connection.ref} value={connection.ref}>
                {connection.ref} ({connection.export_type})
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel id="target-schema-label">Schema</InputLabel>
          <Select
            labelId="target-schema-label"
            label="Schema"
            value={target.schema}
            disabled={loadingSchemas || !target.connection_ref}
            onChange={(event) =>
              updateTarget({ schema: event.target.value, table_name: "", primary_keys: [] })
            }
          >
            {schemas.map((schema) => (
              <MenuItem key={schema} value={schema}>
                {schema}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 180 }}>
          <InputLabel id="target-table-label">Table</InputLabel>
          <Select
            labelId="target-table-label"
            label="Table"
            value={target.table_name}
            disabled={loadingTables || !target.schema}
            onChange={(event) => updateTarget({ table_name: event.target.value, primary_keys: [] })}
          >
            {tables.map((table) => (
              <MenuItem key={table} value={table}>
                {table}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Stack>

      <FormControl size="small" sx={{ maxWidth: 360 }}>
        <InputLabel id="target-on-conflict-label">on_conflict</InputLabel>
        <Select
          labelId="target-on-conflict-label"
          label="on_conflict"
          value={target.on_conflict}
          onChange={(event) => updateTarget({ on_conflict: event.target.value })}
        >
          {ON_CONFLICT_OPTIONS.map((option) => (
            <MenuItem key={option} value={option}>
              {option}
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {target.on_conflict === "IGNORE_AND_INSERT_UNPROCESSED" && (
        <CreateOnTargetPanel
          connectionRef={target.connection_ref}
          mode="COPY_FROM_TABLE"
          destinationValue={target.unprocessed_table ?? ""}
          onDestinationChange={(value) => updateTarget({ unprocessed_table: value || null })}
          migrationId={migrationId}
          blueprintSequence={blueprint.sequence_order}
          sourceSchema={target.schema}
          sourceTable={target.table_name}
          targetSchema={target.schema}
          targetTable={target.table_name}
          primaryKeyColumns={target.primary_keys}
          targetColumns={columns}
          destinationLabel="Unprocessed table (schema.table)"
          helperText="Copies the target table structure (no data) on the target connection."
        />
      )}

      {target.on_conflict === "IGNORE_AND_LOG" && (
        <CreateOnTargetPanel
          connectionRef={target.connection_ref}
          mode="AUDIT_TABLE"
          destinationValue={target.audit_table ?? ""}
          onDestinationChange={(value) => updateTarget({ audit_table: value || null })}
          migrationId={migrationId}
          blueprintSequence={blueprint.sequence_order}
          targetSchema={target.schema}
          targetTable={target.table_name}
          primaryKeyColumns={target.primary_keys}
          targetColumns={columns}
          destinationLabel="Audit table (schema.table)"
          helperText="Proposed from migration and blueprint context (§12.4). Edit before create if needed."
        />
      )}

      <Box>
        <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
          Primary keys
        </Typography>
        {loadingColumns && (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, py: 1 }}>
            <CircularProgress size={18} />
            <Typography variant="body2" color="text.secondary">
              Loading target columns…
            </Typography>
          </Box>
        )}
        {!loadingColumns && columns.length === 0 && (
          <Typography variant="body2" color="text.secondary">
            Select a target table to load primary key candidates.
          </Typography>
        )}
        <FormGroup row>
          {columns.map((column) => (
            <FormControlLabel
              key={column.name}
              control={
                <Checkbox
                  size="small"
                  checked={target.primary_keys.includes(column.name)}
                  onChange={() => togglePrimaryKey(column.name)}
                />
              }
              label={`${column.name} (${column.data_type})`}
            />
          ))}
        </FormGroup>
      </Box>
    </Stack>
  );
}
