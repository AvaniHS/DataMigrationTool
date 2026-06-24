import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import { DatabaseConnectionFieldsForm } from "@/components/connections/DatabaseConnectionFieldsForm";
import { EntraAuthFieldsForm } from "@/components/connections/EntraAuthFieldsForm";
import type { ConnectorFormProps } from "@/components/connections/connectorRegistry";
import { POSTGRES_SSL_MODES } from "@/components/connections/types";

export function PostgresqlForm({
  authMethod,
  sqlFields,
  postgresSslMode,
  azureEntra,
  onSqlFieldsChange,
  onPostgresSslModeChange,
  onAzureEntraChange,
}: ConnectorFormProps) {
  return (
    <Stack spacing={1.5}>
      <DatabaseConnectionFieldsForm
        value={sqlFields}
        onChange={onSqlFieldsChange}
        hideCredentials={authMethod.startsWith("entra_")}
        requireCredentials={authMethod === "password"}
      />
      {authMethod === "password" && (
        <FormControl fullWidth size="small">
          <InputLabel id="postgres-sslmode-label">SSL mode</InputLabel>
          <Select
            labelId="postgres-sslmode-label"
            label="SSL mode"
            value={postgresSslMode}
            onChange={(event) => onPostgresSslModeChange(event.target.value as typeof postgresSslMode)}
          >
            {POSTGRES_SSL_MODES.map((mode) => (
              <MenuItem key={mode} value={mode}>
                {mode}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}
      {authMethod.startsWith("entra_") && (
        <EntraAuthFieldsForm
          authMethod={authMethod}
          value={azureEntra}
          onChange={onAzureEntraChange}
        />
      )}
    </Stack>
  );
}
