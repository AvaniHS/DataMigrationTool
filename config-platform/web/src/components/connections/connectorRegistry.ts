import { LocalCsvForm } from "@/components/connections/connectors/LocalCsvForm";
import { MysqlForm } from "@/components/connections/connectors/MysqlForm";
import { MssqlOnPremForm } from "@/components/connections/connectors/MssqlOnPremForm";
import { AzureSqlDatabaseForm } from "@/components/connections/connectors/AzureSqlDatabaseForm";
import { PostgresqlForm } from "@/components/connections/connectors/PostgresqlForm";
import { S3BucketForm } from "@/components/connections/connectors/S3BucketForm";
import type { ConnectorCatalogItem } from "@/components/connections/types";
import type { ComponentType } from "react";
import type { S3BucketFields, SqlDatabaseFields } from "@/components/connections/types";

export type ConnectorFormProps = {
  authMethod: string;
  sqlFields: SqlDatabaseFields;
  s3Fields: S3BucketFields;
  azureServer: string;
  onSqlFieldsChange: (nextValue: SqlDatabaseFields) => void;
  onS3FieldsChange: (nextValue: S3BucketFields) => void;
  onAzureServerChange: (value: string) => void;
};

export const CONNECTOR_FORM_REGISTRY: Record<string, ComponentType<ConnectorFormProps>> = {
  mysql: MysqlForm,
  postgresql: PostgresqlForm,
  mssql_onprem: MssqlOnPremForm,
  azure_sql_database: AzureSqlDatabaseForm,
  csv_s3_bucket: S3BucketForm,
  local_csv: LocalCsvForm,
};

export function getConnectorFormComponent(connectorId: string): ComponentType<ConnectorFormProps> | null {
  return CONNECTOR_FORM_REGISTRY[connectorId] ?? null;
}

export function catalogByCategory(
  catalog: ConnectorCatalogItem[],
  category: "database" | "file",
): ConnectorCatalogItem[] {
  return catalog.filter((item) => item.category === category);
}

export function findCatalogItem(
  catalog: ConnectorCatalogItem[],
  connectorId: string,
): ConnectorCatalogItem | undefined {
  return catalog.find((item) => item.connector_id === connectorId);
}
