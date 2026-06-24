import { useCallback, useEffect, useState } from "react";
import { getApiErrorMessage } from "@/api/errors";
import {
  createConnection,
  deleteConnection,
  getConnection,
  listConnections,
  testConnection,
  updateConnection,
} from "@/api/connections";
import type {
  ConnectionListItem,
  ConnectionSaveRequest,
} from "@/components/connections/types";

type UseConnectionsResult = {
  connections: ConnectionListItem[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  remove: (ref: string) => Promise<void>;
  save: (body: ConnectionSaveRequest, existingRef?: string) => Promise<void>;
  loadRecord: (ref: string) => Promise<ConnectionSaveRequest>;
  runTest: (body: ConnectionSaveRequest) => Promise<{ message: string; verificationToken: string }>;
};

export function useConnections(): UseConnectionsResult {
  const [connections, setConnections] = useState<ConnectionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setConnections(await listConnections());
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const remove = useCallback(
    async (ref: string) => {
      await deleteConnection(ref);
      await refresh();
    },
    [refresh],
  );

  const save = useCallback(
    async (body: ConnectionSaveRequest, existingRef?: string) => {
      if (existingRef) {
        await updateConnection(existingRef, body);
      } else {
        await createConnection(body);
      }
      await refresh();
    },
    [refresh],
  );

  const loadRecord = useCallback(async (ref: string) => {
    const record = await getConnection(ref);
    return {
      ref: record.ref,
      connector_id: record.connector_id,
      connector_payload: record.connector_payload,
      secret_ref: record.secret_ref,
      verification_token: "",
    };
  }, []);

  const runTest = useCallback(async (body: ConnectionSaveRequest) => {
    const response = await testConnection({
      connector_id: body.connector_id,
      connector_payload: body.connector_payload,
    });
    if (!response.success || !response.verification_token) {
      throw new Error(response.message || "Connection test failed.");
    }
    return { message: response.message, verificationToken: response.verification_token };
  }, []);

  return {
    connections,
    loading,
    error,
    refresh,
    remove,
    save,
    loadRecord,
    runTest,
  };
}
