export type ConnectionType = "MYSQL" | "MSSQL" | "POSTGRESQL" | "CSV_S3_BUCKET";

export type DatabaseConnectionFields = {
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  use_advanced_string: boolean;
  connection_string: string | null;
};

export type S3ConnectionFields = {
  s3_bucket_uri: string;
  aws_region: string;
};

export type ConnectionListItem = {
  ref: string;
  type: ConnectionType;
  summary: string;
  last_tested_at: string | null;
  updated_at: string;
};

export type ConnectionRecord = {
  ref: string;
  type: ConnectionType;
  secret_ref: string | null;
  database: DatabaseConnectionFields | null;
  s3: S3ConnectionFields | null;
  created_at: string;
  updated_at: string;
  last_tested_at: string | null;
};

export type ConnectionTestRequest = {
  type: ConnectionType;
  database?: DatabaseConnectionFields | null;
  s3?: S3ConnectionFields | null;
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

export const CONNECTION_TYPE_OPTIONS: {
  value: ConnectionType;
  label: string;
  defaultPort: number;
}[] = [
  { value: "MYSQL", label: "MySQL", defaultPort: 3306 },
  { value: "POSTGRESQL", label: "PostgreSQL", defaultPort: 5432 },
  { value: "MSSQL", label: "Microsoft SQL Server", defaultPort: 1433 },
  { value: "CSV_S3_BUCKET", label: "CSV on S3", defaultPort: 0 },
];

export function createEmptyDatabaseFields(port: number): DatabaseConnectionFields {
  return {
    host: "",
    port,
    database: "",
    username: "",
    password: "",
    use_advanced_string: false,
    connection_string: null,
  };
}

export function createEmptyS3Fields(): S3ConnectionFields {
  return {
    s3_bucket_uri: "",
    aws_region: "us-east-1",
  };
}

export function defaultPortForType(type: ConnectionType): number {
  return CONNECTION_TYPE_OPTIONS.find((option) => option.value === type)?.defaultPort ?? 3306;
}
