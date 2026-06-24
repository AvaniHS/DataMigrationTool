import Alert from "@mui/material/Alert";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import type { ConnectorFormProps } from "@/components/connections/connectorRegistry";

export function AzureSqlDatabaseForm({
  authMethod,
  sqlFields,
  azureServer,
  onSqlFieldsChange,
  onAzureServerChange,
}: ConnectorFormProps) {
  const update = (patch: Partial<typeof sqlFields>) => {
    onSqlFieldsChange({ ...sqlFields, ...patch });
  };

  return (
    <Stack spacing={1.5}>
      {authMethod !== "sql_login" && (
        <Alert severity="warning">
          Entra authentication ships in P1.2/P1.3. Use SQL login for now.
        </Alert>
      )}
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
        onChange={(event) => update({ database: event.target.value })}
        required
      />
      <TextField
        size="small"
        label="Username"
        value={sqlFields.username}
        onChange={(event) => update({ username: event.target.value })}
        required
      />
      <TextField
        size="small"
        label="Password"
        type="password"
        value={sqlFields.password}
        onChange={(event) => update({ password: event.target.value })}
      />
    </Stack>
  );
}
