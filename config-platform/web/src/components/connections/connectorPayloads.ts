import type { ConnectorCatalogItem } from "@/components/connections/types";
import {
  createEmptyS3Fields,
  createEmptySqlFields,
  type S3BucketFields,
  type SqlDatabaseFields,
} from "@/components/connections/types";

export function defaultAuthMethod(catalogItem: ConnectorCatalogItem): string {
  return catalogItem.auth_methods[0]?.id ?? "";
}

export function buildConnectorPayload(
  connectorId: string,
  authMethod: string,
  sqlFields: SqlDatabaseFields,
  s3Fields: S3BucketFields,
  azureServer?: string,
): Record<string, unknown> {
  if (connectorId === "csv_s3_bucket") {
    return {
      auth_method: authMethod,
      ...s3Fields,
    };
  }

  if (connectorId === "azure_sql_database") {
    return {
      auth_method: authMethod,
      server: azureServer ?? sqlFields.host,
      database: sqlFields.database,
      username: sqlFields.username,
      password: sqlFields.password,
      use_advanced_string: sqlFields.use_advanced_string,
      connection_string: sqlFields.connection_string,
    };
  }

  if (connectorId === "postgresql") {
    return {
      auth_method: authMethod,
      ...sqlFields,
      sslmode: "prefer",
    };
  }

  if (connectorId === "mssql_onprem") {
    return {
      auth_method: authMethod,
      ...sqlFields,
      domain: "",
    };
  }

  if (connectorId === "local_csv") {
    return {
      location_kind: authMethod === "platform_staging" ? "platform_staging" : "local_path",
      file_path: "",
      staging_file_id: "",
    };
  }

  return {
    auth_method: authMethod,
    ...sqlFields,
  };
}

export function parseSqlFieldsFromPayload(payload: Record<string, unknown>): SqlDatabaseFields {
  return {
    host: String(payload.host ?? payload.server ?? ""),
    port: Number(payload.port ?? 3306),
    database: String(payload.database ?? ""),
    username: String(payload.username ?? ""),
    password: String(payload.password ?? ""),
    use_advanced_string: Boolean(payload.use_advanced_string),
    connection_string: (payload.connection_string as string | null) ?? null,
  };
}

export function parseS3FieldsFromPayload(payload: Record<string, unknown>): S3BucketFields {
  return {
    s3_bucket_uri: String(payload.s3_bucket_uri ?? ""),
    aws_region: String(payload.aws_region ?? "us-east-1"),
  };
}

export function initialSqlFieldsForConnector(connectorId: string): SqlDatabaseFields {
  return createEmptySqlFields(connectorId);
}

export function initialS3Fields(): S3BucketFields {
  return createEmptyS3Fields();
}
