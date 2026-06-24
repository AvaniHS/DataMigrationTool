import { describe, expect, it } from "vitest";
import {
  buildConnectorPayload,
  defaultAuthMethod,
  initialSqlFieldsForConnector,
  parseAzureEntraFromPayload,
  parseSqlFieldsFromPayload,
} from "@/components/connections/connectorPayloads";
import { isP12AuthMethod } from "@/components/connections/connectorRegistry";
import type { ConnectorCatalogItem } from "@/components/connections/types";
import { createEmptyS3Fields } from "@/components/connections/types";

const mysqlCatalog: ConnectorCatalogItem = {
  connector_id: "mysql",
  label: "MySQL",
  description: "",
  category: "database",
  export_type: "MYSQL",
  auth_methods: [{ id: "password", label: "Password", delivery_phase: "P1.2" }],
};

describe("connectorPayloads", () => {
  it("defaults auth method from catalog metadata", () => {
    expect(defaultAuthMethod(mysqlCatalog)).toBe("password");
  });

  it("builds mysql payload with ssl_enabled", () => {
    const sqlFields = { ...initialSqlFieldsForConnector("mysql"), host: "db.local", database: "app" };
    const payload = buildConnectorPayload("mysql", "password", sqlFields, createEmptyS3Fields(), {
      mysqlSslEnabled: true,
    });
    expect(payload).toMatchObject({
      auth_method: "password",
      host: "db.local",
      database: "app",
      ssl_enabled: true,
    });
  });

  it("builds mssql windows login payload with domain", () => {
    const sqlFields = {
      ...initialSqlFieldsForConnector("mssql_onprem"),
      host: "sql01",
      database: "app",
      username: "svc",
      password: "secret",
    };
    const payload = buildConnectorPayload("mssql_onprem", "windows_login", sqlFields, createEmptyS3Fields(), {
      mssqlDomain: "CORP",
    });
    expect(payload).toMatchObject({
      auth_method: "windows_login",
      domain: "CORP",
      username: "svc",
    });
  });

  it("builds s3 access_key payload", () => {
    const payload = buildConnectorPayload(
      "csv_s3_bucket",
      "access_key",
      initialSqlFieldsForConnector("mysql"),
      {
        s3_bucket_uri: "s3://bucket/prefix/",
        aws_region: "us-east-1",
        access_key_id: "AKIA",
        secret_access_key: "secret",
      },
    );
    expect(payload).toMatchObject({
      auth_method: "access_key",
      access_key_id: "AKIA",
      secret_access_key: "secret",
    });
  });

  it("builds postgresql entra password payload", () => {
    const sqlFields = {
      ...initialSqlFieldsForConnector("postgresql"),
      host: "pg.postgres.database.azure.com",
      database: "app",
    };
    const payload = buildConnectorPayload("postgresql", "entra_password", sqlFields, createEmptyS3Fields(), {
      azureEntra: {
        tenant_id: "tenant",
        client_id: "client",
        client_secret: "",
        entra_user: "user@contoso.com",
        entra_password: "pass",
        managed_identity_client_id: "",
      },
    });
    expect(payload).toMatchObject({
      auth_method: "entra_password",
      entra_user: "user@contoso.com",
      sslmode: "require",
    });
  });

  it("builds local_csv platform staging payload", () => {
    const payload = buildConnectorPayload(
      "local_csv",
      "platform_staging",
      initialSqlFieldsForConnector("mysql"),
      createEmptyS3Fields(),
      {
        localCsv: {
          file_path: "",
          staging_file_id: "abc123",
          parse_options: {
            delimiter: ";",
            quote: "'",
            header_row: 2,
            encoding: "utf-8",
          },
        },
      },
    );
    expect(payload).toMatchObject({
      location_kind: "platform_staging",
      staging_file_id: "abc123",
      parse_options: { delimiter: ";", header_row: 2 },
    });
  });

  it("parses extended entra fields from payload", () => {
    expect(
      parseAzureEntraFromPayload({
        tenant_id: "t",
        client_id: "c",
        entra_user: "u",
        managed_identity_client_id: "mi",
      }),
    ).toMatchObject({
      tenant_id: "t",
      entra_user: "u",
      managed_identity_client_id: "mi",
    });
  });

  it("parses sql fields from legacy host or azure server keys", () => {
    expect(parseSqlFieldsFromPayload({ host: "a", port: 5432 })).toMatchObject({ host: "a", port: 5432 });
    expect(parseSqlFieldsFromPayload({ server: "azure.example.net", database: "x" })).toMatchObject({
      host: "azure.example.net",
      database: "x",
    });
  });
});

describe("isP12AuthMethod", () => {
  it("recognizes P1.2 auth methods", () => {
    expect(isP12AuthMethod("mssql_onprem", "windows_integrated")).toBe(true);
    expect(isP12AuthMethod("azure_sql_database", "entra_service_principal")).toBe(true);
    expect(isP12AuthMethod("mssql_onprem", "ntlm")).toBe(false);
  });
});
