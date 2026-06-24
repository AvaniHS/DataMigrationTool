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
};

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

export type ConnectionTestRequest = {
  connector_id: string;
  connector_payload: Record<string, unknown>;
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
  };
}
