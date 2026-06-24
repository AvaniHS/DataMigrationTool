import { describe, expect, it } from "vitest";
import {
  buildConnectorPayload,
  defaultAuthMethod,
  initialSqlFieldsForConnector,
  parseSqlFieldsFromPayload,
} from "@/components/connections/connectorPayloads";
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

  it("builds mysql payload with sql fields and auth method", () => {
    const sqlFields = { ...initialSqlFieldsForConnector("mysql"), host: "db.local", database: "app" };
    const payload = buildConnectorPayload("mysql", "password", sqlFields, createEmptyS3Fields());
    expect(payload).toMatchObject({
      auth_method: "password",
      host: "db.local",
      database: "app",
      port: 3306,
    });
  });

  it("builds azure sql payload with server field", () => {
    const sqlFields = {
      ...initialSqlFieldsForConnector("azure_sql_database"),
      database: "warehouse",
      username: "admin",
      password: "secret",
    };
    const payload = buildConnectorPayload(
      "azure_sql_database",
      "sql_login",
      sqlFields,
      createEmptyS3Fields(),
      "myserver.database.windows.net",
    );
    expect(payload).toEqual({
      auth_method: "sql_login",
      server: "myserver.database.windows.net",
      database: "warehouse",
      username: "admin",
      password: "secret",
      use_advanced_string: false,
      connection_string: null,
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
