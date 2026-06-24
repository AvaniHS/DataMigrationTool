import { useCallback, useEffect, useState } from "react";
import { getApiErrorMessage } from "@/api/errors";
import {
  addBlueprint,
  createMigration,
  deleteBlueprint,
  deleteMigration,
  duplicateBlueprint,
  getMigration,
  listMigrations,
  reorderBlueprints,
  updateMigration,
} from "@/api/migrations";
import type {
  CreateMigrationRequest,
  MigrationListItem,
  MigrationRecord,
  UpdateMigrationRequest,
} from "@/components/migrations/types";

type UseMigrationsResult = {
  migrations: MigrationListItem[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  create: (body: CreateMigrationRequest) => Promise<MigrationRecord>;
  remove: (migrationId: string) => Promise<void>;
  load: (migrationId: string) => Promise<MigrationRecord>;
  save: (migrationId: string, body: UpdateMigrationRequest) => Promise<MigrationRecord>;
  addBlueprint: (migrationId: string) => Promise<MigrationRecord>;
  removeBlueprint: (migrationId: string, sequenceOrder: number) => Promise<MigrationRecord>;
  copyBlueprint: (migrationId: string, sequenceOrder: number) => Promise<MigrationRecord>;
  moveBlueprint: (migrationId: string, sequenceOrders: number[]) => Promise<MigrationRecord>;
};

export function useMigrations(): UseMigrationsResult {
  const [migrations, setMigrations] = useState<MigrationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setMigrations(await listMigrations());
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const create = useCallback(async (body: CreateMigrationRequest) => {
    const record = await createMigration(body);
    await refresh();
    return record;
  }, [refresh]);

  const remove = useCallback(
    async (migrationId: string) => {
      await deleteMigration(migrationId);
      await refresh();
    },
    [refresh],
  );

  const load = useCallback(async (migrationId: string) => getMigration(migrationId), []);

  const save = useCallback(async (migrationId: string, body: UpdateMigrationRequest) => {
    return updateMigration(migrationId, body);
  }, []);

  const addBlueprintAction = useCallback(async (migrationId: string) => {
    return addBlueprint(migrationId);
  }, []);

  const removeBlueprint = useCallback(async (migrationId: string, sequenceOrder: number) => {
    return deleteBlueprint(migrationId, sequenceOrder);
  }, []);

  const copyBlueprint = useCallback(async (migrationId: string, sequenceOrder: number) => {
    return duplicateBlueprint(migrationId, sequenceOrder);
  }, []);

  const moveBlueprint = useCallback(async (migrationId: string, sequenceOrders: number[]) => {
    return reorderBlueprints(migrationId, sequenceOrders);
  }, []);

  return {
    migrations,
    loading,
    error,
    refresh,
    create,
    remove,
    load,
    save,
    addBlueprint: addBlueprintAction,
    removeBlueprint,
    copyBlueprint,
    moveBlueprint,
  };
}
