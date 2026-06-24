import { describe, expect, it } from "vitest";
import {
  buildConnectorPayload,
  defaultAuthMethod,
  initialSqlFieldsForConnector,
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
