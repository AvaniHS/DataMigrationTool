import { apiFetch } from "./client";
import type {
  ConnectionListItem,
  ConnectionRecord,
  ConnectionSaveRequest,
  ConnectionTestRequest,
  ConnectionTestResponse,
} from "@/components/connections/types";

export function listConnections(): Promise<ConnectionListItem[]> {
  return apiFetch<ConnectionListItem[]>("/connections");
}

export function getConnection(ref: string): Promise<ConnectionRecord> {
  return apiFetch<ConnectionRecord>(`/connections/${encodeURIComponent(ref)}`);
}

export function testConnection(body: ConnectionTestRequest): Promise<ConnectionTestResponse> {
  return apiFetch<ConnectionTestResponse>("/connections/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function createConnection(body: ConnectionSaveRequest): Promise<ConnectionRecord> {
  return apiFetch<ConnectionRecord>("/connections", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function updateConnection(ref: string, body: ConnectionSaveRequest): Promise<ConnectionRecord> {
  return apiFetch<ConnectionRecord>(`/connections/${encodeURIComponent(ref)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function deleteConnection(ref: string): Promise<void> {
  return apiFetch<void>(`/connections/${encodeURIComponent(ref)}`, {
    method: "DELETE",
  });
}

export function exportConnections(): Promise<Record<string, Record<string, string>>> {
  return apiFetch<Record<string, Record<string, string>>>("/connections/export");
}
