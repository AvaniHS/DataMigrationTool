import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { getApiErrorMessage } from "@/api/errors";
import { BlueprintList } from "@/components/config_wizard/BlueprintList";
import { BlueprintWizard } from "@/components/config_wizard/BlueprintWizard";
import { MigrationHeaderForm } from "@/components/config_wizard/MigrationHeaderForm";
import { useConnections } from "@/components/connections/useConnections";
import type { MigrationRecord } from "@/components/migrations/types";
import { ErrorAlertWithRetry } from "@/components/shared/ErrorAlertWithRetry";
import { PageHeader } from "@/components/shared/PageHeader";
import { SchemaTree } from "@/components/shared/SchemaTree";
import { useMigrations } from "@/hooks/useMigrations";

export function MigrationDetailView() {
  const { migrationId } = useParams<{ migrationId: string }>();
  const {
    load,
    save,
    addBlueprint,
    removeBlueprint,
    copyBlueprint,
    moveBlueprint,
  } = useMigrations();
  const { connections, loading: connectionsLoading } = useConnections();

  const [migration, setMigration] = useState<MigrationRecord | null>(null);
  const [header, setHeader] = useState({
    migration_id: migrationId ?? "",
    client_id: "",
    version: "",
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [blueprintBusy, setBlueprintBusy] = useState(false);
  const [selectedSequenceOrder, setSelectedSequenceOrder] = useState<number | null>(null);
  const [introspectionConnectionRef, setIntrospectionConnectionRef] = useState("");

  const refreshMigration = useCallback(async () => {
    if (!migrationId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const record = await load(migrationId);
      setMigration(record);
      setHeader({
        migration_id: record.migration_id,
        client_id: record.client_id,
        version: record.version,
      });
      setSelectedSequenceOrder((current) => current ?? record.blueprints[0]?.sequence_order ?? null);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [load, migrationId]);

  useEffect(() => {
    void refreshMigration();
  }, [refreshMigration]);

  useEffect(() => {
    if (!introspectionConnectionRef && connections.length > 0) {
      setIntrospectionConnectionRef(connections[0].ref);
    }
  }, [connections, introspectionConnectionRef]);

  const selectedBlueprint = useMemo(() => {
    if (!migration || selectedSequenceOrder === null) {
      return null;
    }
    return migration.blueprints.find((item) => item.sequence_order === selectedSequenceOrder) ?? null;
  }, [migration, selectedSequenceOrder]);

  const introspectionConnection = connections.find((item) => item.ref === introspectionConnectionRef);

  const persistMigration = async (next: MigrationRecord) => {
    if (!migrationId) {
      return;
    }
    const saved = await save(migrationId, {
      client_id: next.client_id,
      version: next.version,
      blueprints: next.blueprints,
    });
    setMigration(saved);
    setHeader({
      migration_id: saved.migration_id,
      client_id: saved.client_id,
      version: saved.version,
    });
  };

  const handleSaveHeader = async () => {
    if (!migration) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await persistMigration({
        ...migration,
        client_id: header.client_id,
        version: header.version,
      });
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const runBlueprintAction = async (action: () => Promise<MigrationRecord>) => {
    setBlueprintBusy(true);
    setError(null);
    try {
      const updated = await action();
      setMigration(updated);
      if (
        selectedSequenceOrder !== null &&
        !updated.blueprints.some((item) => item.sequence_order === selectedSequenceOrder)
      ) {
        setSelectedSequenceOrder(updated.blueprints[0]?.sequence_order ?? null);
      }
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setBlueprintBusy(false);
    }
  };

  const handleMoveBlueprint = async (sequenceOrder: number, direction: "up" | "down") => {
    if (!migration || !migrationId) {
      return;
    }
    const ordered = [...migration.blueprints].sort(
      (left, right) => left.sequence_order - right.sequence_order,
    );
    const index = ordered.findIndex((item) => item.sequence_order === sequenceOrder);
    if (index < 0) {
      return;
    }
    const swapIndex = direction === "up" ? index - 1 : index + 1;
    if (swapIndex < 0 || swapIndex >= ordered.length) {
      return;
    }
    const reordered = [...ordered];
    [reordered[index], reordered[swapIndex]] = [reordered[swapIndex], reordered[index]];
    await runBlueprintAction(() =>
      moveBlueprint(
        migrationId,
        reordered.map((item) => item.sequence_order),
      ),
    );
  };

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error && !migration) {
    return <ErrorAlertWithRetry message={error} onRetry={() => void refreshMigration()} />;
  }

  if (!migration) {
    return <Alert severity="warning">Migration not found.</Alert>;
  }

  return (
    <>
      <PageHeader title="Migration workspace" />

      <Stack spacing={2}>
        {error && <ErrorAlertWithRetry message={error} onRetry={() => void refreshMigration()} />}

        <Paper variant="outlined" sx={{ p: 1.5 }}>
          <MigrationHeaderForm values={header} saving={saving} onChange={setHeader} />
          <Box sx={{ mt: 1.5 }}>
            <Button size="small" variant="contained" disabled={saving} onClick={() => void handleSaveHeader()}>
              Save header
            </Button>
          </Box>
        </Paper>

        <Paper variant="outlined" sx={{ p: 1.5 }}>
          <BlueprintList
            blueprints={migration.blueprints}
            selectedSequenceOrder={selectedSequenceOrder}
            busy={blueprintBusy}
            onAdd={() =>
              void runBlueprintAction(() => {
                if (!migrationId) {
                  throw new Error("Missing migration id.");
                }
                return addBlueprint(migrationId);
              })
            }
            onSelect={setSelectedSequenceOrder}
            onDuplicate={(sequenceOrder) =>
              void runBlueprintAction(() => {
                if (!migrationId) {
                  throw new Error("Missing migration id.");
                }
                return copyBlueprint(migrationId, sequenceOrder);
              })
            }
            onDelete={(sequenceOrder) => {
              if (!window.confirm(`Delete blueprint ${sequenceOrder}?`)) {
                return;
              }
              void runBlueprintAction(() => {
                if (!migrationId) {
                  throw new Error("Missing migration id.");
                }
                return removeBlueprint(migrationId, sequenceOrder);
              });
            }}
            onMoveUp={(sequenceOrder) => void handleMoveBlueprint(sequenceOrder, "up")}
            onMoveDown={(sequenceOrder) => void handleMoveBlueprint(sequenceOrder, "down")}
          />
        </Paper>

        <Paper variant="outlined" sx={{ p: 1.5 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Schema introspection
          </Typography>
          <FormControl size="small" sx={{ minWidth: 240, mb: 1 }}>
            <InputLabel id="introspection-connection-label">Connection</InputLabel>
            <Select
              labelId="introspection-connection-label"
              label="Connection"
              value={introspectionConnectionRef}
              disabled={connectionsLoading || connections.length === 0}
              onChange={(event) => setIntrospectionConnectionRef(event.target.value)}
            >
              {connections.map((connection) => (
                <MenuItem key={connection.ref} value={connection.ref}>
                  {connection.ref} ({connection.export_type})
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          {connections.length === 0 && (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Add connections under Connect before browsing schema metadata.
            </Typography>
          )}
          <SchemaTree
            connectionRef={introspectionConnectionRef}
            isFileConnection={
              introspectionConnection?.export_type === "CSV_S3_BUCKET" ||
              introspectionConnection?.export_type === "LOCAL_CSV"
            }
          />
        </Paper>

        {selectedBlueprint && migrationId && (
          <Paper variant="outlined" sx={{ p: 1.5 }}>
            <BlueprintWizard
              migrationId={migration.migration_id}
              clientId={migration.client_id}
              version={migration.version}
              blueprint={selectedBlueprint}
              connections={connections}
              onSave={async (blueprint) => {
                const nextBlueprints = migration.blueprints.map((item) =>
                  item.sequence_order === blueprint.sequence_order ? blueprint : item,
                );
                await persistMigration({
                  ...migration,
                  blueprints: nextBlueprints,
                });
              }}
            />
          </Paper>
        )}
      </Stack>
    </>
  );
}
