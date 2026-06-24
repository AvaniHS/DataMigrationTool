import type { ConnectorCatalogItem } from "@/components/connections/types";
import {
  createEmptyAzureEntraFields,
  createEmptyLocalCsvFields,
  createEmptyMysqlSslFields,
  createEmptyPostgresClientCertFields,
  createEmptyS3Fields,
  createEmptySqlFields,
  type AzureEntraFields,
  type LocalCsvFields,
  type MysqlSslFields,
  type PostgresClientCertFields,
  type PostgresSslMode,
  type S3BucketFields,
  type SqlDatabaseFields,
  MYSQL_SSL_MODES,
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
    mysqlSslFields?: MysqlSslFields;
    postgresClientCertFields?: PostgresClientCertFields;
    rdsAwsRegion?: string;
    postgresSslMode?: PostgresSslMode;
    azureEntra?: AzureEntraFields;
    localCsv?: LocalCsvFields;
  } = {},
): Record<string, unknown> {
  const {
    azureServer,
    mssqlDomain = "",
    mysqlSslEnabled = false,
    mysqlSslFields = createEmptyMysqlSslFields(),
    postgresClientCertFields = createEmptyPostgresClientCertFields(),
    rdsAwsRegion = "",
    postgresSslMode = "prefer",
    azureEntra = createEmptyAzureEntraFields(),
    localCsv = createEmptyLocalCsvFields(),
  } = options;

  if (connectorId === "csv_s3_bucket") {
    return {
      auth_method: authMethod,
      s3_bucket_uri: s3Fields.s3_bucket_uri,
      aws_region: s3Fields.aws_region,
      access_key_id: s3Fields.access_key_id,
      secret_access_key: s3Fields.secret_access_key,
      session_token: s3Fields.session_token,
      role_arn: s3Fields.role_arn,
      external_id: s3Fields.external_id,
    };
  }

  if (connectorId === "azure_sql_database") {
    const base = {
      auth_method: authMethod,
      server: azureServer ?? sqlFields.host,
      database: sqlFields.database,
      encrypt: true,
      trust_server_certificate: false,
      use_advanced_string: false,
      connection_string: null,
    };
    if (authMethod === "sql_login") {
      return {
        ...base,
        username: sqlFields.username,
        password: sqlFields.password,
        use_advanced_string: sqlFields.use_advanced_string,
        connection_string: sqlFields.connection_string,
      };
    }
    if (authMethod === "entra_service_principal") {
      return {
        ...base,
        tenant_id: azureEntra.tenant_id,
        client_id: azureEntra.client_id,
        client_secret: azureEntra.client_secret,
      };
    }
    if (authMethod === "entra_password") {
      return {
        ...base,
        tenant_id: azureEntra.tenant_id,
        client_id: azureEntra.client_id,
        entra_user: azureEntra.entra_user,
        entra_password: azureEntra.entra_password,
      };
    }
    if (authMethod === "entra_managed_identity") {
      return {
        ...base,
        managed_identity_client_id: azureEntra.managed_identity_client_id,
      };
    }
    return base;
  }

  if (connectorId === "postgresql") {
    const base = {
      auth_method: authMethod,
      host: sqlFields.host,
      port: sqlFields.port,
      database: sqlFields.database,
      use_advanced_string: sqlFields.use_advanced_string,
      connection_string: sqlFields.connection_string,
    };
    if (authMethod === "password") {
      return {
        ...base,
        username: sqlFields.username,
        password: sqlFields.password,
        sslmode: postgresSslMode,
      };
    }
    if (authMethod === "password_ssl_client_cert") {
      return {
        ...base,
        username: sqlFields.username,
        password: sqlFields.password,
        sslmode: "verify-full",
        ...postgresClientCertFields,
      };
    }
    if (authMethod === "postgresql_rds_iam") {
      return {
        ...base,
        username: sqlFields.username,
        aws_region: rdsAwsRegion,
      };
    }
    return {
      ...base,
      sslmode: "require",
      tenant_id: azureEntra.tenant_id,
      client_id: azureEntra.client_id,
      client_secret: azureEntra.client_secret,
      entra_user: azureEntra.entra_user,
      entra_password: azureEntra.entra_password,
      managed_identity_client_id: azureEntra.managed_identity_client_id,
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
    const base = {
      auth_method: authMethod,
      host: sqlFields.host,
      port: sqlFields.port,
      database: sqlFields.database,
      use_advanced_string: sqlFields.use_advanced_string,
      connection_string: sqlFields.connection_string,
    };
    if (authMethod === "password") {
      return {
        ...base,
        username: sqlFields.username,
        password: sqlFields.password,
        ssl_enabled: mysqlSslEnabled,
      };
    }
    if (authMethod === "password_ssl") {
      return {
        ...base,
        username: sqlFields.username,
        password: sqlFields.password,
        ssl_mode: mysqlSslFields.ssl_mode,
        ssl_ca_path: mysqlSslFields.ssl_ca_path,
      };
    }
    if (authMethod === "mysql_rds_iam") {
      return {
        ...base,
        username: sqlFields.username,
        aws_region: rdsAwsRegion,
      };
    }
    return {
      ...base,
      ssl_enabled: true,
      tenant_id: azureEntra.tenant_id,
      client_id: azureEntra.client_id,
      client_secret: azureEntra.client_secret,
      entra_user: azureEntra.entra_user,
      managed_identity_client_id: azureEntra.managed_identity_client_id,
    };
  }

  if (connectorId === "local_csv") {
    return {
      location_kind: authMethod === "platform_staging" ? "platform_staging" : "local_path",
      file_path: localCsv.file_path,
      staging_file_id: localCsv.staging_file_id,
      parse_options: localCsv.parse_options,
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
    session_token: String(payload.session_token ?? ""),
    role_arn: String(payload.role_arn ?? ""),
    external_id: String(payload.external_id ?? ""),
  };
}

export function parseMysqlSslFieldsFromPayload(payload: Record<string, unknown>): MysqlSslFields {
  const mode = String(payload.ssl_mode ?? "PREFERRED");
  return {
    ssl_mode: MYSQL_SSL_MODES.includes(mode as MysqlSslFields["ssl_mode"])
      ? (mode as MysqlSslFields["ssl_mode"])
      : "PREFERRED",
    ssl_ca_path: String(payload.ssl_ca_path ?? ""),
  };
}

export function parsePostgresClientCertFromPayload(
  payload: Record<string, unknown>,
): PostgresClientCertFields {
  return {
    sslrootcert: String(payload.sslrootcert ?? ""),
    sslcert: String(payload.sslcert ?? ""),
    sslkey: String(payload.sslkey ?? ""),
  };
}

export function parseRdsAwsRegionFromPayload(payload: Record<string, unknown>): string {
  return String(payload.aws_region ?? "");
}

export function parseAzureEntraFromPayload(payload: Record<string, unknown>): AzureEntraFields {
  return {
    tenant_id: String(payload.tenant_id ?? ""),
    client_id: String(payload.client_id ?? ""),
    client_secret: String(payload.client_secret ?? ""),
    entra_user: String(payload.entra_user ?? ""),
    entra_password: String(payload.entra_password ?? ""),
    managed_identity_client_id: String(payload.managed_identity_client_id ?? ""),
  };
}

export function parseMssqlDomainFromPayload(payload: Record<string, unknown>): string {
  return String(payload.domain ?? "");
}

export function parseMysqlSslEnabled(payload: Record<string, unknown>): boolean {
  return Boolean(payload.ssl_enabled);
}

export function parseLocalCsvFromPayload(payload: Record<string, unknown>): LocalCsvFields {
  const parseOptions = (payload.parse_options as Record<string, unknown> | undefined) ?? {};
  return {
    file_path: String(payload.file_path ?? ""),
    staging_file_id: String(payload.staging_file_id ?? ""),
    parse_options: {
      delimiter: String(parseOptions.delimiter ?? ","),
      quote: String(parseOptions.quote ?? '"'),
      header_row: Number(parseOptions.header_row ?? 1),
      encoding: String(parseOptions.encoding ?? "utf-8"),
    },
  };
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

export function initialLocalCsvFields(): LocalCsvFields {
  return createEmptyLocalCsvFields();
}

export function initialMysqlSslFields(): MysqlSslFields {
  return createEmptyMysqlSslFields();
}

export function initialPostgresClientCertFields(): PostgresClientCertFields {
  return createEmptyPostgresClientCertFields();
}
