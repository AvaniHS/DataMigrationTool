import Alert from "@mui/material/Alert";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import type { ConnectorFormProps } from "@/components/connections/connectorRegistry";

export function AzureSqlDatabaseForm({
  authMethod,
  sqlFields,
  azureServer,
  azureEntra,
  onSqlFieldsChange,
  onAzureServerChange,
  onAzureEntraChange,
}: ConnectorFormProps) {
  const updateSql = (patch: Partial<typeof sqlFields>) => {
    onSqlFieldsChange({ ...sqlFields, ...patch });
  };

  const updateEntra = (patch: Partial<typeof azureEntra>) => {
    onAzureEntraChange({ ...azureEntra, ...patch });
  };

  return (
    <Stack spacing={1.5}>
      <TextField
        size="small"
        label="Server"
        helperText="e.g. myserver.database.windows.net"
        value={azureServer}
        onChange={(event) => onAzureServerChange(event.target.value)}
        required
      />
      <TextField
        size="small"
        label="Database"
        value={sqlFields.database}
        onChange={(event) => updateSql({ database: event.target.value })}
        required
      />

      {authMethod === "sql_login" && (
        <>
          <Alert severity="info" sx={{ py: 0.5 }}>
            SQL login often uses <code>user@servername</code> as the username.
          </Alert>
          <TextField
            size="small"
            label="Username"
            value={sqlFields.username}
            onChange={(event) => updateSql({ username: event.target.value })}
            required
          />
          <TextField
            size="small"
            label="Password"
            type="password"
            value={sqlFields.password}
            onChange={(event) => updateSql({ password: event.target.value })}
          />
        </>
      )}

      {authMethod === "entra_service_principal" && (
        <>
          <TextField
            size="small"
            label="Tenant ID"
            value={azureEntra.tenant_id}
            onChange={(event) => updateEntra({ tenant_id: event.target.value })}
            required
          />
          <TextField
            size="small"
            label="Client ID"
            value={azureEntra.client_id}
            onChange={(event) => updateEntra({ client_id: event.target.value })}
            required
          />
          <TextField
            size="small"
            label="Client secret"
            type="password"
            value={azureEntra.client_secret}
            onChange={(event) => updateEntra({ client_secret: event.target.value })}
            required
          />
        </>
      )}
    </Stack>
  );
}
