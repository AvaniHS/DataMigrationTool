import { useEffect, useMemo, useState } from "react";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox";
import Drawer from "@mui/material/Drawer";
import IconButton from "@mui/material/IconButton";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import {
  DataGrid,
  type GridColDef,
  type GridRenderCellParams,
  type GridRenderEditCellParams,
} from "@mui/x-data-grid";
import { listColumns, listFileColumns, type ColumnNode } from "@/api/introspection";
import type { Blueprint } from "@/components/migrations/types";
import type { ConnectionListItem } from "@/components/connections/types";
import { SqlCodeEditor } from "@/components/shared/SqlCodeEditor";
import {
  SOURCE_TYPE_OPTIONS,
  buildDirectSourceOptions,
  collectSourceAliases,
  isFileBackedSource,
} from "./blueprintHelpers";

type StepMappingsProps = {
  blueprint: Blueprint;
  connections: ConnectionListItem[];
  targetColumns: ColumnNode[];
  onChange: (blueprint: Blueprint) => void;
};

export function StepMappings({
  blueprint,
  connections,
  targetColumns,
  onChange,
}: StepMappingsProps) {
  const [derivationsOpen, setDerivationsOpen] = useState(false);
  const [sourceColumns, setSourceColumns] = useState<Record<string, ColumnNode[]>>({});
  const aliases = collectSourceAliases(blueprint);

  useEffect(() => {
    let cancelled = false;

    async function loadSourceColumns() {
      const next: Record<string, ColumnNode[]> = {};
      const root = blueprint.sources.root_table;
      if (root.connection_ref) {
        const key = sourceCacheKey(root.connection_ref, root, connections);
        if (isFileBackedSource(root.connection_ref, connections) && root.file_name) {
          next[key] = await listFileColumns(root.connection_ref, root.file_name);
        } else if (root.schema && root.table_name) {
          next[key] = await listColumns(root.connection_ref, root.schema, root.table_name);
        }
      }
      for (const join of blueprint.sources.joins) {
        if (!join.connection_ref) {
          continue;
        }
        const key = sourceCacheKey(join.connection_ref, join, connections);
        if (isFileBackedSource(join.connection_ref, connections) && join.file_name) {
          next[key] = await listFileColumns(join.connection_ref, join.file_name);
        } else if (join.schema && join.table_name) {
          next[key] = await listColumns(join.connection_ref, join.schema, join.table_name);
        }
      }
      if (!cancelled) {
        setSourceColumns(next);
      }
    }

    void loadSourceColumns();
    return () => {
      cancelled = true;
    };
  }, [blueprint.sources, connections]);

  const directOptions = useMemo(
    () => buildDirectSourceOptions(blueprint, sourceColumns, connections),
    [blueprint, sourceColumns, connections],
  );

  const derivationOptions = blueprint.derivations.map(
    (derivation) => `derivations.${derivation.variable_name}`,
  );

  const updateMapping = (targetColumn: string, patch: Partial<Blueprint["mappings"][number]>) => {
    onChange({
      ...blueprint,
      mappings: blueprint.mappings.map((mapping) =>
        mapping.target_column === targetColumn ? { ...mapping, ...patch } : mapping,
      ),
    });
  };

  const columns: GridColDef[] = [
    { field: "target_column", headerName: "Target", flex: 1, minWidth: 120, editable: false },
    {
      field: "source_type",
      headerName: "Type",
      width: 130,
      editable: true,
      type: "singleSelect",
      valueOptions: [...SOURCE_TYPE_OPTIONS],
    },
    {
      field: "source_value",
      headerName: "Source value",
      flex: 1.4,
      minWidth: 180,
      editable: true,
      renderEditCell: (params: GridRenderEditCellParams) => {
        const mapping = params.row as Blueprint["mappings"][number];
        if (mapping.source_type === "DIRECT") {
          return (
            <Select
              size="small"
              fullWidth
              value={mapping.source_value}
              onChange={(event) =>
                updateMapping(mapping.target_column, { source_value: event.target.value })
              }
            >
              {directOptions.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          );
        }
        if (mapping.source_type === "DERIVED") {
          return (
            <Select
              size="small"
              fullWidth
              value={mapping.source_value}
              onChange={(event) =>
                updateMapping(mapping.target_column, { source_value: event.target.value })
              }
            >
              {derivationOptions.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          );
        }
        return (
          <TextField
            size="small"
            fullWidth
            value={mapping.source_value}
            onChange={(event) =>
              updateMapping(mapping.target_column, { source_value: event.target.value })
            }
          />
        );
      },
      renderCell: (params: GridRenderCellParams) => (
        <Typography variant="body2" noWrap title={String(params.value ?? "")}>
          {String(params.value ?? "")}
        </Typography>
      ),
    },
    { field: "cast_to", headerName: "Cast to", flex: 1, minWidth: 120, editable: true },
    {
      field: "is_nullable",
      headerName: "Nullable",
      width: 90,
      editable: true,
      type: "boolean",
      renderCell: (params: GridRenderCellParams) => (
        <Checkbox checked={Boolean(params.value)} disabled size="small" />
      ),
    },
  ];

  const rows = blueprint.mappings.map((mapping, index) => ({
    id: mapping.target_column || `row-${index}`,
    ...mapping,
  }));

  return (
    <Stack spacing={1.5}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="body2" color="text.secondary">
          Source aliases: {aliases.length > 0 ? aliases.join(", ") : "none"} · Target columns:{" "}
          {targetColumns.length}
        </Typography>
        <Button size="small" variant="outlined" onClick={() => setDerivationsOpen(true)}>
          Derivations ({blueprint.derivations.length})
        </Button>
      </Stack>

      <Box sx={{ height: 360, width: "100%" }}>
        <DataGrid
          rows={rows}
          columns={columns}
          disableRowSelectionOnClick
          density="compact"
          hideFooter={rows.length <= 10}
          processRowUpdate={(newRow) => {
            const { id: _id, ...mapping } = newRow as Blueprint["mappings"][number] & { id: string };
            onChange({
              ...blueprint,
              mappings: blueprint.mappings.map((item) =>
                item.target_column === mapping.target_column ? mapping : item,
              ),
            });
            return newRow;
          }}
          onProcessRowUpdateError={() => undefined}
          sx={{
            border: 1,
            borderColor: "divider",
            "& .MuiDataGrid-columnHeaders": { minHeight: 36, maxHeight: 36 },
          }}
        />
      </Box>

      <Drawer anchor="right" open={derivationsOpen} onClose={() => setDerivationsOpen(false)}>
        <Box sx={{ width: 420, p: 2 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
            <Typography variant="subtitle1">Derivations</Typography>
            <Button
              size="small"
              startIcon={<AddIcon />}
              onClick={() =>
                onChange({
                  ...blueprint,
                  derivations: [
                    ...blueprint.derivations,
                    { variable_name: "", expression: "" },
                  ],
                })
              }
            >
              Add
            </Button>
          </Stack>
          {blueprint.derivations.length === 0 && (
            <Typography variant="body2" color="text.secondary">
              No derivations yet. Add reusable expressions referenced as derivations.name in mappings.
            </Typography>
          )}
          <Stack spacing={1.5}>
            {blueprint.derivations.map((derivation, index) => (
              <Box key={`derivation-${index}`} sx={{ border: 1, borderColor: "divider", p: 1, borderRadius: 1 }}>
                <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                  <TextField
                    size="small"
                    label="Variable name"
                    value={derivation.variable_name}
                    onChange={(event) => {
                      const derivations = blueprint.derivations.map((item, itemIndex) =>
                        itemIndex === index
                          ? { ...item, variable_name: event.target.value }
                          : item,
                      );
                      onChange({ ...blueprint, derivations });
                    }}
                    sx={{ flex: 1 }}
                  />
                  <IconButton
                    size="small"
                    aria-label={`Delete derivation ${index + 1}`}
                    onClick={() =>
                      onChange({
                        ...blueprint,
                        derivations: blueprint.derivations.filter((_, itemIndex) => itemIndex !== index),
                      })
                    }
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Stack>
                <SqlCodeEditor
                  label="Expression"
                  value={derivation.expression}
                  onChange={(value) => {
                    const derivations = blueprint.derivations.map((item, itemIndex) =>
                      itemIndex === index ? { ...item, expression: value } : item,
                    );
                    onChange({ ...blueprint, derivations });
                  }}
                  minRows={4}
                />
              </Box>
            ))}
          </Stack>
        </Box>
      </Drawer>
    </Stack>
  );
}

function sourceCacheKey(
  connectionRef: string,
  source: { schema: string; table_name: string; file_name?: string | null },
  connections: ConnectionListItem[],
): string {
  if (isFileBackedSource(connectionRef, connections)) {
    return `${connectionRef}:file:${source.file_name ?? ""}`;
  }
  return `${connectionRef}:table:${source.schema}.${source.table_name}`;
}
