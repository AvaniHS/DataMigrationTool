import type { ConnectorCatalogItem } from "@/components/connections/types";
import {
  createEmptyAzureEntraFields,
  createEmptyS3Fields,
  createEmptySqlFields,
  type AzureEntraFields,
  type PostgresSslMode,
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
  options: {
    azureServer?: string;
    mssqlDomain?: string;
    mysqlSslEnabled?: boolean;
    postgresSslMode?: PostgresSslMode;
    azureEntra?: AzureEntraFields;
  } = {},
): Record<string, unknown> {
  const {
    azureServer,
    mssqlDomain = "",
    mysqlSslEnabled = false,
    postgresSslMode = "prefer",
    azureEntra = createEmptyAzureEntraFields(),
  } = options;

  if (connectorId === "csv_s3_bucket") {
    return {
      auth_method: authMethod,
      s3_bucket_uri: s3Fields.s3_bucket_uri,
      aws_region: s3Fields.aws_region,
      access_key_id: s3Fields.access_key_id,
      secret_access_key: s3Fields.secret_access_key,
    };
  }

  if (connectorId === "azure_sql_database") {
    if (authMethod === "entra_service_principal") {
      return {
        auth_method: authMethod,
        server: azureServer ?? sqlFields.host,
        database: sqlFields.database,
        tenant_id: azureEntra.tenant_id,
        client_id: azureEntra.client_id,
        client_secret: azureEntra.client_secret,
        encrypt: true,
        trust_server_certificate: false,
        use_advanced_string: false,
        connection_string: null,
      };
    }
    return {
      auth_method: authMethod,
      server: azureServer ?? sqlFields.host,
      database: sqlFields.database,
      username: sqlFields.username,
      password: sqlFields.password,
      encrypt: true,
      trust_server_certificate: false,
      use_advanced_string: sqlFields.use_advanced_string,
      connection_string: sqlFields.connection_string,
    };
  }

  if (connectorId === "postgresql") {
    return {
      auth_method: authMethod,
      ...sqlFields,
      sslmode: postgresSslMode,
    };
  }

  if (connectorId === "mssql_onprem") {
    return {
      auth_method: authMethod,
      host: sqlFields.host,
      port: sqlFields.port,
      database: sqlFields.database,
      username: sqlFields.username,
      password: sqlFields.password,
      domain: mssqlDomain,
      encrypt: true,
      trust_server_certificate: false,
      use_advanced_string: sqlFields.use_advanced_string,
      connection_string: sqlFields.connection_string,
    };
  }

  if (connectorId === "mysql") {
    return {
      auth_method: authMethod,
      ...sqlFields,
      ssl_enabled: mysqlSslEnabled,
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
    access_key_id: String(payload.access_key_id ?? ""),
    secret_access_key: String(payload.secret_access_key ?? ""),
  };
}

export function parseAzureEntraFromPayload(payload: Record<string, unknown>): AzureEntraFields {
  return {
    tenant_id: String(payload.tenant_id ?? ""),
    client_id: String(payload.client_id ?? ""),
    client_secret: String(payload.client_secret ?? ""),
  };
}

export function parseMssqlDomainFromPayload(payload: Record<string, unknown>): string {
  return String(payload.domain ?? "");
}

export function parseMysqlSslEnabled(payload: Record<string, unknown>): boolean {
  return Boolean(payload.ssl_enabled);
}

export function parsePostgresSslMode(payload: Record<string, unknown>): PostgresSslMode {
  const value = String(payload.sslmode ?? "prefer");
  if (
    value === "disable" ||
    value === "allow" ||
    value === "prefer" ||
    value === "require" ||
    value === "verify-ca" ||
    value === "verify-full"
  ) {
    return value;
  }
  return "prefer";
}

export function initialSqlFieldsForConnector(connectorId: string): SqlDatabaseFields {
  return createEmptySqlFields(connectorId);
}

export function initialS3Fields(): S3BucketFields {
  return createEmptyS3Fields();
}

export function initialAzureEntraFields(): AzureEntraFields {
  return createEmptyAzureEntraFields();
}
