import { useEffect, useMemo, useState } from "react";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import FormControl from "@mui/material/FormControl";
import IconButton from "@mui/material/IconButton";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import type { Blueprint, JoinSource } from "@/components/migrations/types";
import type { ConnectionListItem } from "@/components/connections/types";
import { SchemaTree } from "@/components/shared/SchemaTree";
import { SqlCodeEditor } from "@/components/shared/SqlCodeEditor";
import {
  JOIN_TYPE_OPTIONS,
  createEmptyJoin,
  isFileBackedSource,
  isFileConnectionType,
} from "./blueprintHelpers";

type SelectionTarget = "root" | number;

type StepSourcesJoinsProps = {
  blueprint: Blueprint;
  connections: ConnectionListItem[];
  onChange: (blueprint: Blueprint) => void;
};

export function StepSourcesJoins({ blueprint, connections, onChange }: StepSourcesJoinsProps) {
  const [treeConnectionRef, setTreeConnectionRef] = useState(
    blueprint.sources.root_table.connection_ref || connections[0]?.ref || "",
  );
  const [selectionTarget, setSelectionTarget] = useState<SelectionTarget>("root");

  useEffect(() => {
    if (!treeConnectionRef && connections[0]?.ref) {
      setTreeConnectionRef(connections[0].ref);
    }
  }, [connections, treeConnectionRef]);

  const treeConnection = connections.find((item) => item.ref === treeConnectionRef);
  const isFileTree = treeConnection ? isFileConnectionType(treeConnection.export_type) : false;

  const updateRoot = (patch: Partial<Blueprint["sources"]["root_table"]>) => {
    onChange({
      ...blueprint,
      sources: {
        ...blueprint.sources,
        root_table: { ...blueprint.sources.root_table, ...patch },
      },
    });
  };

  const updateJoin = (index: number, patch: Partial<JoinSource>) => {
    const joins = blueprint.sources.joins.map((join, joinIndex) =>
      joinIndex === index ? { ...join, ...patch } : join,
    );
    onChange({
      ...blueprint,
      sources: { ...blueprint.sources, joins },
    });
  };

  const applyTableSelection = (schema: string, table: string) => {
    if (selectionTarget === "root") {
      updateRoot({
        connection_ref: treeConnectionRef,
        schema,
        table_name: table,
        file_name: null,
      });
      return;
    }
    updateJoin(selectionTarget, {
      connection_ref: treeConnectionRef,
      schema,
      table_name: table,
      file_name: null,
    });
  };

  const applyFileSelection = (fileName: string) => {
    if (selectionTarget === "root") {
      updateRoot({
        connection_ref: treeConnectionRef,
        file_name: fileName,
        schema: "",
        table_name: "",
      });
      return;
    }
    updateJoin(selectionTarget, {
      connection_ref: treeConnectionRef,
      file_name: fileName,
      schema: "",
      table_name: "",
    });
  };

  const selectionLabel = useMemo(() => {
    if (selectionTarget === "root") {
      return "Root table";
    }
    return `Join ${selectionTarget + 1}`;
  }, [selectionTarget]);

  const rootIsFile = isFileBackedSource(blueprint.sources.root_table.connection_ref, connections);

  return (
    <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ alignItems: "stretch" }}>
      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Schema browser
        </Typography>
        <FormControl size="small" fullWidth sx={{ mb: 1 }}>
          <InputLabel id="b1-tree-connection-label">Browse connection</InputLabel>
          <Select
            labelId="b1-tree-connection-label"
            label="Browse connection"
            value={treeConnectionRef}
            onChange={(event) => setTreeConnectionRef(event.target.value)}
          >
            {connections.map((connection) => (
              <MenuItem key={connection.ref} value={connection.ref}>
                {connection.ref} ({connection.export_type})
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" fullWidth sx={{ mb: 1 }}>
          <InputLabel id="b1-selection-target-label">Apply selection to</InputLabel>
          <Select
            labelId="b1-selection-target-label"
            label="Apply selection to"
            value={selectionTarget === "root" ? "root" : String(selectionTarget)}
            onChange={(event) => {
              const value = event.target.value;
              setSelectionTarget(value === "root" ? "root" : Number(value));
            }}
          >
            <MenuItem value="root">Root table</MenuItem>
            {blueprint.sources.joins.map((join, index) => (
              <MenuItem key={`join-target-${index}`} value={String(index)}>
                Join {index + 1} ({join.alias || "no alias"})
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1 }}>
          Click a table or file in the tree to assign it to {selectionLabel.toLowerCase()}.
        </Typography>
        <SchemaTree
          connectionRef={treeConnectionRef}
          isFileConnection={isFileTree}
          onSelectTable={applyTableSelection}
          onSelectFile={applyFileSelection}
        />
      </Box>

      <Box sx={{ flex: 1.2, minWidth: 0 }}>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Root source
        </Typography>
        <Stack spacing={1}>
          <FormControl size="small" fullWidth>
            <InputLabel id="root-connection-label">Connection</InputLabel>
            <Select
              labelId="root-connection-label"
              label="Connection"
              value={blueprint.sources.root_table.connection_ref}
              onChange={(event) => updateRoot({ connection_ref: event.target.value })}
            >
              {connections.map((connection) => (
                <MenuItem key={connection.ref} value={connection.ref}>
                  {connection.ref}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            size="small"
            label="Alias"
            value={blueprint.sources.root_table.alias}
            onChange={(event) => updateRoot({ alias: event.target.value })}
          />
          {rootIsFile ? (
            <TextField
              size="small"
              label="File name"
              value={blueprint.sources.root_table.file_name ?? ""}
              onChange={(event) => updateRoot({ file_name: event.target.value })}
            />
          ) : (
            <Stack direction="row" spacing={1}>
              <TextField
                size="small"
                label="Schema"
                value={blueprint.sources.root_table.schema}
                onChange={(event) => updateRoot({ schema: event.target.value })}
                sx={{ flex: 1 }}
              />
              <TextField
                size="small"
                label="Table"
                value={blueprint.sources.root_table.table_name}
                onChange={(event) => updateRoot({ table_name: event.target.value })}
                sx={{ flex: 1 }}
              />
            </Stack>
          )}
          <TextField
            size="small"
            label="Comment"
            value={blueprint.sources.root_table.comment ?? ""}
            onChange={(event) => updateRoot({ comment: event.target.value || null })}
          />
        </Stack>

        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mt: 2, mb: 1 }}>
          <Typography variant="subtitle2">Joins</Typography>
          <Button
            size="small"
            startIcon={<AddIcon />}
            onClick={() =>
              onChange({
                ...blueprint,
                sources: {
                  ...blueprint.sources,
                  joins: [...blueprint.sources.joins, createEmptyJoin()],
                },
              })
            }
          >
            Add join
          </Button>
        </Stack>

        {blueprint.sources.joins.length === 0 && (
          <Typography variant="body2" color="text.secondary">
            No joins configured. Add a join to combine additional sources.
          </Typography>
        )}

        {blueprint.sources.joins.map((join, index) => {
          const joinIsFile = isFileBackedSource(join.connection_ref, connections);
          return (
            <Accordion key={`join-${index}`} defaultExpanded={index === 0} disableGutters sx={{ mb: 1 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="body2">
                  Join {index + 1}: {join.alias || "unnamed"} ({join.join_type})
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Stack spacing={1}>
                  <Stack direction="row" spacing={1}>
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                      <InputLabel id={`join-type-${index}`}>Type</InputLabel>
                      <Select
                        labelId={`join-type-${index}`}
                        label="Type"
                        value={join.join_type}
                        onChange={(event) =>
                          updateJoin(index, {
                            join_type: event.target.value as JoinSource["join_type"],
                          })
                        }
                      >
                        {JOIN_TYPE_OPTIONS.map((option) => (
                          <MenuItem key={option} value={option}>
                            {option}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                    <FormControl size="small" sx={{ flex: 1 }}>
                      <InputLabel id={`join-connection-${index}`}>Connection</InputLabel>
                      <Select
                        labelId={`join-connection-${index}`}
                        label="Connection"
                        value={join.connection_ref}
                        onChange={(event) => updateJoin(index, { connection_ref: event.target.value })}
                      >
                        {connections.map((connection) => (
                          <MenuItem key={connection.ref} value={connection.ref}>
                            {connection.ref}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                    <TextField
                      size="small"
                      label="Alias"
                      value={join.alias}
                      onChange={(event) => updateJoin(index, { alias: event.target.value })}
                      sx={{ width: 120 }}
                    />
                    <IconButton
                      size="small"
                      aria-label={`Delete join ${index + 1}`}
                      onClick={() =>
                        onChange({
                          ...blueprint,
                          sources: {
                            ...blueprint.sources,
                            joins: blueprint.sources.joins.filter((_, joinIndex) => joinIndex !== index),
                          },
                        })
                      }
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Stack>
                  {joinIsFile ? (
                    <TextField
                      size="small"
                      label="File name"
                      value={join.file_name ?? ""}
                      onChange={(event) => updateJoin(index, { file_name: event.target.value })}
                    />
                  ) : (
                    <Stack direction="row" spacing={1}>
                      <TextField
                        size="small"
                        label="Schema"
                        value={join.schema}
                        onChange={(event) => updateJoin(index, { schema: event.target.value })}
                        sx={{ flex: 1 }}
                      />
                      <TextField
                        size="small"
                        label="Table"
                        value={join.table_name}
                        onChange={(event) => updateJoin(index, { table_name: event.target.value })}
                        sx={{ flex: 1 }}
                      />
                    </Stack>
                  )}
                  <TextField
                    size="small"
                    label="Comment"
                    value={join.comment ?? ""}
                    onChange={(event) => updateJoin(index, { comment: event.target.value || null })}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Conditions
                  </Typography>
                  {join.conditions.map((condition, conditionIndex) => (
                    <Stack key={`join-${index}-cond-${conditionIndex}`} spacing={0.75}>
                      <SqlCodeEditor
                        label="Left expression"
                        value={condition.left_expression}
                        onChange={(value) => {
                          const conditions = join.conditions.map((item, itemIndex) =>
                            itemIndex === conditionIndex ? { ...item, left_expression: value } : item,
                          );
                          updateJoin(index, { conditions });
                        }}
                        minRows={2}
                      />
                      <TextField
                        size="small"
                        label="Operator"
                        value={condition.operator}
                        onChange={(event) => {
                          const conditions = join.conditions.map((item, itemIndex) =>
                            itemIndex === conditionIndex
                              ? { ...item, operator: event.target.value }
                              : item,
                          );
                          updateJoin(index, { conditions });
                        }}
                        sx={{ maxWidth: 120 }}
                      />
                      <SqlCodeEditor
                        label="Right expression"
                        value={condition.right_expression}
                        onChange={(value) => {
                          const conditions = join.conditions.map((item, itemIndex) =>
                            itemIndex === conditionIndex ? { ...item, right_expression: value } : item,
                          );
                          updateJoin(index, { conditions });
                        }}
                        minRows={2}
                      />
                    </Stack>
                  ))}
                  <Button
                    size="small"
                    onClick={() =>
                      updateJoin(index, {
                        conditions: [
                          ...join.conditions,
                          { left_expression: "", operator: "=", right_expression: "" },
                        ],
                      })
                    }
                  >
                    Add condition
                  </Button>
                </Stack>
              </AccordionDetails>
            </Accordion>
          );
        })}
      </Box>
    </Stack>
  );
}
