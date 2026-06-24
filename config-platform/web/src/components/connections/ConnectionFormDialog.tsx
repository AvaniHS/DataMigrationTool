import { useEffect, useMemo, useState } from "react";
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { listConnectors } from "@/api/connectors";
import {
  buildConnectorPayload,
  defaultAuthMethod,
  initialAzureEntraFields,
  initialLocalCsvFields,
  initialMysqlSslFields,
  initialPostgresClientCertFields,
  initialS3Fields,
  initialSqlFieldsForConnector,
  parseAzureEntraFromPayload,
  parseLocalCsvFromPayload,
  parseMssqlDomainFromPayload,
  parseMysqlSslEnabled,
  parseMysqlSslFieldsFromPayload,
  parsePostgresClientCertFromPayload,
  parsePostgresSslMode,
  parseRdsAwsRegionFromPayload,
  parseS3FieldsFromPayload,
  parseSqlFieldsFromPayload,
} from "@/components/connections/connectorPayloads";
import {
  catalogByCategory,
  findCatalogItem,
  getConnectorFormComponent,
} from "@/components/connections/connectorRegistry";
import type {
  AzureEntraFields,
  ConnectionSaveRequest,
  ConnectorCatalogItem,
  ConnectorCategory,
  LocalCsvFields,
  MysqlSslFields,
  PostgresClientCertFields,
  PostgresSslMode,
  S3BucketFields,
  SqlDatabaseFields,
} from "@/components/connections/types";
import { getApiErrorMessage } from "@/api/errors";

type ConnectionFormDialogProps = {
  open: boolean;
  editRef?: string;
  initialValues?: ConnectionSaveRequest | null;
  onClose: () => void;
  onTest: (body: ConnectionSaveRequest) => Promise<{ message: string; verificationToken: string }>;
  onSave: (body: ConnectionSaveRequest, existingRef?: string) => Promise<void>;
};

type TestState = "idle" | "testing" | "passed" | "failed";

export function ConnectionFormDialog({
  open,
  editRef,
  initialValues,
  onClose,
  onTest,
  onSave,
}: ConnectionFormDialogProps) {
  const [catalog, setCatalog] = useState<ConnectorCatalogItem[]>([]);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [connectionReference, setConnectionReference] = useState("");
  const [category, setCategory] = useState<ConnectorCategory>("database");
  const [connectorId, setConnectorId] = useState("mysql");
  const [authMethod, setAuthMethod] = useState("password");
  const [sqlFields, setSqlFields] = useState<SqlDatabaseFields>(initialSqlFieldsForConnector("mysql"));
  const [s3Fields, setS3Fields] = useState<S3BucketFields>(initialS3Fields());
  const [azureServer, setAzureServer] = useState("");
  const [mssqlDomain, setMssqlDomain] = useState("");
  const [mysqlSslEnabled, setMysqlSslEnabled] = useState(false);
  const [mysqlSslFields, setMysqlSslFields] = useState<MysqlSslFields>(initialMysqlSslFields());
  const [postgresClientCertFields, setPostgresClientCertFields] = useState<PostgresClientCertFields>(
    initialPostgresClientCertFields(),
  );
  const [rdsAwsRegion, setRdsAwsRegion] = useState("");
  const [postgresSslMode, setPostgresSslMode] = useState<PostgresSslMode>("prefer");
  const [azureEntra, setAzureEntra] = useState<AzureEntraFields>(initialAzureEntraFields());
  const [localCsvFields, setLocalCsvFields] = useState<LocalCsvFields>(initialLocalCsvFields());
  const [verificationToken, setVerificationToken] = useState<string | null>(null);
  const [testState, setTestState] = useState<TestState>("idle");
  const [testMessage, setTestMessage] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const isEditing = Boolean(editRef);
  const selectedConnector = findCatalogItem(catalog, connectorId);
  const ConnectorForm = getConnectorFormComponent(connectorId);

  useEffect(() => {
    if (!open) {
      return;
    }
    void listConnectors()
      .then(setCatalog)
      .catch((error) => setCatalogError(getApiErrorMessage(error)));
  }, [open]);

  useEffect(() => {
    if (!open) {
      return;
    }
    if (initialValues) {
      const payload = initialValues.connector_payload;
      setConnectionReference(initialValues.ref);
      setConnectorId(initialValues.connector_id);
      setAuthMethod(
        String(
          payload.location_kind ??
            payload.auth_method ??
            defaultAuthMethod(findCatalogItem(catalog, initialValues.connector_id) ?? catalog[0]),
        ),
      );
      setSqlFields(parseSqlFieldsFromPayload(payload));
      setS3Fields(parseS3FieldsFromPayload(payload));
      setLocalCsvFields(parseLocalCsvFromPayload(payload));
      setAzureServer(String(payload.server ?? payload.host ?? ""));
      setMssqlDomain(parseMssqlDomainFromPayload(payload));
      setMysqlSslEnabled(parseMysqlSslEnabled(payload));
      setMysqlSslFields(parseMysqlSslFieldsFromPayload(payload));
      setPostgresClientCertFields(parsePostgresClientCertFromPayload(payload));
      setRdsAwsRegion(parseRdsAwsRegionFromPayload(payload));
      setPostgresSslMode(parsePostgresSslMode(payload));
      setAzureEntra(parseAzureEntraFromPayload(payload));
      const item = findCatalogItem(catalog, initialValues.connector_id);
      if (item) {
        setCategory(item.category);
      }
    } else {
      setConnectionReference("");
      setCategory("database");
      setConnectorId("mysql");
      setAuthMethod("password");
      setSqlFields(initialSqlFieldsForConnector("mysql"));
      setS3Fields(initialS3Fields());
      setAzureServer("");
      setMssqlDomain("");
      setMysqlSslEnabled(false);
      setMysqlSslFields(initialMysqlSslFields());
      setPostgresClientCertFields(initialPostgresClientCertFields());
      setRdsAwsRegion("");
      setPostgresSslMode("prefer");
      setAzureEntra(initialAzureEntraFields());
      setLocalCsvFields(initialLocalCsvFields());
    }
    setVerificationToken(null);
    setTestState("idle");
    setTestMessage(null);
    setSaveError(null);
  }, [open, initialValues, catalog]);

  const connectorPayload = useMemo(
    () =>
      buildConnectorPayload(connectorId, authMethod, sqlFields, s3Fields, {
        azureServer,
        mssqlDomain,
        mysqlSslEnabled,
        mysqlSslFields,
        postgresClientCertFields,
        rdsAwsRegion,
        postgresSslMode,
        azureEntra,
        localCsv: localCsvFields,
      }),
    [
      authMethod,
      azureEntra,
      azureServer,
      connectorId,
      localCsvFields,
      mssqlDomain,
      mysqlSslEnabled,
      mysqlSslFields,
      postgresClientCertFields,
      rdsAwsRegion,
      postgresSslMode,
      s3Fields,
      sqlFields,
    ],
  );

  const payload = useMemo<ConnectionSaveRequest>(
    () => ({
      ref: connectionReference,
      connector_id: connectorId,
      connector_payload: connectorPayload,
      verification_token: verificationToken ?? "",
    }),
    [connectionReference, connectorId, connectorPayload, verificationToken],
  );

  const invalidateTest = () => {
    setVerificationToken(null);
    setTestState("idle");
    setTestMessage(null);
  };

  const applyConnectorDefaults = (nextConnectorId: string, catalogItems: ConnectorCatalogItem[]) => {
    const item = findCatalogItem(catalogItems, nextConnectorId);
    if (!item) {
      return;
    }
    setCategory(item.category);
    setConnectorId(nextConnectorId);
    setAuthMethod(defaultAuthMethod(item));
    setSqlFields(initialSqlFieldsForConnector(nextConnectorId));
    setS3Fields(initialS3Fields());
    setAzureServer("");
    setMssqlDomain("");
    setMysqlSslEnabled(false);
    setMysqlSslFields(initialMysqlSslFields());
    setPostgresClientCertFields(initialPostgresClientCertFields());
    setRdsAwsRegion("");
    setPostgresSslMode("prefer");
    setAzureEntra(initialAzureEntraFields());
    setLocalCsvFields(initialLocalCsvFields());
    invalidateTest();
  };

  const handleCategoryChange = (nextCategory: ConnectorCategory) => {
    setCategory(nextCategory);
    const first = catalogByCategory(catalog, nextCategory)[0];
    if (first) {
      applyConnectorDefaults(first.connector_id, catalog);
    }
  };

  const handleConnectorChange = (nextConnectorId: string) => {
    applyConnectorDefaults(nextConnectorId, catalog);
  };

  const handleTest = async () => {
    setTestState("testing");
    setTestMessage(null);
    setSaveError(null);
    try {
      const result = await onTest({ ...payload, verification_token: "" });
      setVerificationToken(result.verificationToken);
      setTestState("passed");
      setTestMessage(result.message);
    } catch (error) {
      setTestState("failed");
      setTestMessage(getApiErrorMessage(error));
    }
  };

  const handleSave = async () => {
    if (!verificationToken) {
      setSaveError("Test the connection before saving.");
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      await onSave({ ...payload, verification_token: verificationToken }, editRef);
      onClose();
    } catch (error) {
      setSaveError(getApiErrorMessage(error));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{isEditing ? `Edit connection: ${editRef}` : "Add connection"}</DialogTitle>
      <DialogContent>
        <Stack spacing={1.5} sx={{ mt: 1 }}>
          {catalogError && <Alert severity="error">{catalogError}</Alert>}

          <TextField
            size="small"
            label="Connection ref"
            helperText="Lowercase slug used in config JSON (e.g. client_crm_mysql)"
            value={connectionReference}
            disabled={isEditing}
            onChange={(event) => {
              setConnectionReference(event.target.value.trim().toLowerCase());
              invalidateTest();
            }}
            required
          />

          <FormControl fullWidth size="small">
            <InputLabel id="connector-category-label">Category</InputLabel>
            <Select
              labelId="connector-category-label"
              label="Category"
              value={category}
              onChange={(event) => handleCategoryChange(event.target.value as ConnectorCategory)}
            >
              <MenuItem value="database">Database</MenuItem>
              <MenuItem value="file">File</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth size="small">
            <InputLabel id="connector-id-label">Connector</InputLabel>
            <Select
              labelId="connector-id-label"
              label="Connector"
              value={connectorId}
              onChange={(event) => handleConnectorChange(event.target.value)}
            >
              {catalogByCategory(catalog, category).map((item) => (
                <MenuItem key={item.connector_id} value={item.connector_id}>
                  {item.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {selectedConnector && selectedConnector.auth_methods.length > 1 && (
            <FormControl fullWidth size="small">
              <InputLabel id="auth-method-label">Auth method</InputLabel>
              <Select
                labelId="auth-method-label"
                label="Auth method"
                value={authMethod}
                onChange={(event) => {
                  setAuthMethod(event.target.value);
                  invalidateTest();
                }}
              >
                {selectedConnector.auth_methods.map((method) => (
                  <MenuItem key={method.id} value={method.id}>
                    {method.label} ({method.delivery_phase})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          {ConnectorForm && (
            <ConnectorForm
              authMethod={authMethod}
              connectionReference={connectionReference}
              sqlFields={sqlFields}
              s3Fields={s3Fields}
              localCsvFields={localCsvFields}
              azureServer={azureServer}
              mssqlDomain={mssqlDomain}
              mysqlSslEnabled={mysqlSslEnabled}
              mysqlSslFields={mysqlSslFields}
              postgresClientCertFields={postgresClientCertFields}
              rdsAwsRegion={rdsAwsRegion}
              postgresSslMode={postgresSslMode}
              azureEntra={azureEntra}
              onSqlFieldsChange={(nextValue) => {
                setSqlFields(nextValue);
                invalidateTest();
              }}
              onS3FieldsChange={(nextValue) => {
                setS3Fields(nextValue);
                invalidateTest();
              }}
              onLocalCsvFieldsChange={(nextValue) => {
                setLocalCsvFields(nextValue);
                invalidateTest();
              }}
              onAzureServerChange={(value) => {
                setAzureServer(value);
                invalidateTest();
              }}
              onMssqlDomainChange={(value) => {
                setMssqlDomain(value);
                invalidateTest();
              }}
              onMysqlSslEnabledChange={(value) => {
                setMysqlSslEnabled(value);
                invalidateTest();
              }}
              onMysqlSslFieldsChange={(nextValue) => {
                setMysqlSslFields(nextValue);
                invalidateTest();
              }}
              onPostgresClientCertFieldsChange={(nextValue) => {
                setPostgresClientCertFields(nextValue);
                invalidateTest();
              }}
              onRdsAwsRegionChange={(value) => {
                setRdsAwsRegion(value);
                invalidateTest();
              }}
              onPostgresSslModeChange={(value) => {
                setPostgresSslMode(value);
                invalidateTest();
              }}
              onAzureEntraChange={(nextValue) => {
                setAzureEntra(nextValue);
                invalidateTest();
              }}
            />
          )}

          {testMessage && (
            <Alert severity={testState === "passed" ? "success" : "error"}>{testMessage}</Alert>
          )}
          {saveError && <Alert severity="error">{saveError}</Alert>}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button size="small" onClick={onClose}>
          Cancel
        </Button>
        <Button
          size="small"
          onClick={() => void handleTest()}
          disabled={testState === "testing" || !connectionReference}
        >
          {testState === "testing" ? "Testing…" : "Test connection"}
        </Button>
        <Button
          size="small"
          variant="contained"
          onClick={() => void handleSave()}
          disabled={saving || !verificationToken}
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
}
