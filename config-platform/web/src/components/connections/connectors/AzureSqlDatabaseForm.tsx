import Alert from "@mui/material/Alert";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { EntraAuthFieldsForm } from "@/components/connections/EntraAuthFieldsForm";
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

      {authMethod.startsWith("entra_") && (
        <EntraAuthFieldsForm
          authMethod={authMethod}
          value={azureEntra}
          onChange={onAzureEntraChange}
          showEntraUser={authMethod !== "entra_service_principal"}
        />
      )}
    </Stack>
  );
}
