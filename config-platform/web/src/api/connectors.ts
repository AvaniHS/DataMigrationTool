import { apiFetch } from "./client";
import type { ConnectorCatalogItem } from "@/components/connections/types";

export function listConnectors(): Promise<ConnectorCatalogItem[]> {
  return apiFetch<ConnectorCatalogItem[]>("/connectors");
}

export function getConnectorSchema(connectorId: string): Promise<ConnectorCatalogItem> {
  return apiFetch<ConnectorCatalogItem>(`/connectors/${encodeURIComponent(connectorId)}/schema`);
}
