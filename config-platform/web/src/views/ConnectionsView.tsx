import { useState } from "react";
import { ConnectionFormDialog } from "@/components/connections/ConnectionFormDialog";
import { ConnectionList } from "@/components/connections/ConnectionList";
import { useConnections } from "@/components/connections/useConnections";
import type { ConnectionSaveRequest } from "@/components/connections/types";
import { PageHeader } from "@/components/shared/PageHeader";

export function ConnectionsView() {
  const { connections, loading, error, remove, save, loadRecord, runTest, refresh } = useConnections();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editRef, setEditRef] = useState<string | undefined>();
  const [initialValues, setInitialValues] = useState<ConnectionSaveRequest | null>(null);

  const openCreateDialog = () => {
    setEditRef(undefined);
    setInitialValues(null);
    setDialogOpen(true);
  };

  const openEditDialog = async (ref: string) => {
    const record = await loadRecord(ref);
    setEditRef(ref);
    setInitialValues(record);
    setDialogOpen(true);
  };

  const handleDelete = async (ref: string) => {
    if (!window.confirm(`Delete connection '${ref}'?`)) {
      return;
    }
    await remove(ref);
  };

  return (
    <>
      <PageHeader
        title="Connect"
        description="Register source, target, and file connections. Each connection must pass a live test before it can be saved."
      />

      <ConnectionList
        connections={connections}
        loading={loading}
        error={error}
        onAdd={openCreateDialog}
        onEdit={(ref) => void openEditDialog(ref)}
        onDelete={(ref) => void handleDelete(ref)}
        onRetry={() => void refresh()}
      />

      <ConnectionFormDialog
        open={dialogOpen}
        editRef={editRef}
        initialValues={initialValues}
        onClose={() => setDialogOpen(false)}
        onTest={runTest}
        onSave={save}
      />
    </>
  );
}
