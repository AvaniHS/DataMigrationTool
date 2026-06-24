export type ConnectorCategory = "database" | "file";

export type AuthMethodSchema = {
  id: string;
  label: string;
  delivery_phase: string;
};

export type ConnectorCatalogItem = {
  connector_id: string;
  label: string;
  description: string;
  category: ConnectorCategory;
  export_type: string;
  auth_methods: AuthMethodSchema[];
};

export type SqlDatabaseFields = {
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  use_advanced_string: boolean;
  connection_string: string | null;
};

export type S3BucketFields = {
  s3_bucket_uri: string;
  aws_region: string;
  access_key_id: string;
  secret_access_key: string;
  session_token: string;
  role_arn: string;
  external_id: string;
};

export type MysqlSslMode =
  | "DISABLED"
  | "PREFERRED"
  | "REQUIRED"
  | "VERIFY_CA"
  | "VERIFY_IDENTITY";

export const MYSQL_SSL_MODES: MysqlSslMode[] = [
  "DISABLED",
  "PREFERRED",
  "REQUIRED",
  "VERIFY_CA",
  "VERIFY_IDENTITY",
];

export type MysqlSslFields = {
  ssl_mode: MysqlSslMode;
  ssl_ca_path: string;
};

export type PostgresClientCertFields = {
  sslrootcert: string;
  sslcert: string;
  sslkey: string;
};

export type AzureEntraFields = {
  tenant_id: string;
  client_id: string;
  client_secret: string;
  entra_user: string;
  entra_password: string;
  managed_identity_client_id: string;
};

export type PostgresSslMode =
  | "disable"
  | "allow"
  | "prefer"
  | "require"
  | "verify-ca"
  | "verify-full";

export const POSTGRES_SSL_MODES: PostgresSslMode[] = [
  "disable",
  "allow",
  "prefer",
  "require",
  "verify-ca",
  "verify-full",
];

export type ConnectionListItem = {
  ref: string;
  connector_id: string;
  export_type: string;
  category: ConnectorCategory;
  summary: string;
  last_tested_at: string | null;
  updated_at: string;
};

export type ConnectionRecord = {
  ref: string;
  connector_id: string;
  connector_payload: Record<string, unknown>;
  secret_ref: string | null;
  created_at: string;
  updated_at: string;
  last_tested_at: string | null;
};

export type LocalCsvParseOptions = {
  delimiter: string;
  quote: string;
  header_row: number;
  encoding: string;
};

export type LocalCsvFields = {
  file_path: string;
  staging_file_id: string;
  parse_options: LocalCsvParseOptions;
};

export type ConnectionTestRequest = {
  connector_id: string;
  connector_payload: Record<string, unknown>;
  connection_ref?: string | null;
};

export type StagingUploadResponse = {
  staging_file_id: string;
};

export type ConnectionTestResponse = {
  success: boolean;
  message: string;
  verification_token: string | null;
};

export type ConnectionSaveRequest = ConnectionTestRequest & {
  ref: string;
  secret_ref?: string | null;
  verification_token: string;
};

export const DEFAULT_PORTS: Record<string, number> = {
  mysql: 3306,
  postgresql: 5432,
  mssql_onprem: 1433,
  azure_sql_database: 1433,
};

export function createEmptySqlFields(connectorId: string): SqlDatabaseFields {
  return {
    host: "",
    port: DEFAULT_PORTS[connectorId] ?? 3306,
    database: "",
    username: "",
    password: "",
    use_advanced_string: false,
    connection_string: null,
  };
}

export function createEmptyS3Fields(): S3BucketFields {
  return {
    s3_bucket_uri: "",
    aws_region: "us-east-1",
    access_key_id: "",
    secret_access_key: "",
    session_token: "",
    role_arn: "",
    external_id: "",
  };
}

export function createEmptyMysqlSslFields(): MysqlSslFields {
  return {
    ssl_mode: "PREFERRED",
    ssl_ca_path: "",
  };
}

export function createEmptyPostgresClientCertFields(): PostgresClientCertFields {
  return {
    sslrootcert: "",
    sslcert: "",
    sslkey: "",
  };
}

export function createEmptyAzureEntraFields(): AzureEntraFields {
  return {
    tenant_id: "",
    client_id: "",
    client_secret: "",
    entra_user: "",
    entra_password: "",
    managed_identity_client_id: "",
  };
}

export function createEmptyLocalCsvFields(): LocalCsvFields {
  return {
    file_path: "",
    staging_file_id: "",
    parse_options: {
      delimiter: ",",
      quote: '"',
      header_row: 1,
      encoding: "utf-8",
    },
  };
}
