import Alert from "@mui/material/Alert";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { DatabaseConnectionFieldsForm } from "@/components/connections/DatabaseConnectionFieldsForm";
import type { ConnectorFormProps } from "@/components/connections/connectorRegistry";

export function MssqlOnPremForm({
  authMethod,
  sqlFields,
  mssqlDomain,
  onSqlFieldsChange,
  onMssqlDomainChange,
}: ConnectorFormProps) {
  const showSqlLogin = authMethod === "sql_login";
  const showWindowsLogin = authMethod === "windows_login";
  const showIntegrated = authMethod === "windows_integrated";

  return (
    <Stack spacing={1.5}>
      {showIntegrated && (
        <Alert severity="info">
          Uses the Windows identity of the machine running the config API. The API must run on a
          domain-joined Windows host.
        </Alert>
      )}
      {showWindowsLogin && (
        <TextField
          size="small"
          label="Domain"
          value={mssqlDomain}
          onChange={(event) => onMssqlDomainChange(event.target.value)}
          required
        />
      )}
      <DatabaseConnectionFieldsForm
        value={sqlFields}
        onChange={onSqlFieldsChange}
        hideCredentials={showIntegrated}
        requireCredentials={showSqlLogin || showWindowsLogin}
      />
    </Stack>
  );
}
