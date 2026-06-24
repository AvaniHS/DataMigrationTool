import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { DatabaseConnectionFieldsForm } from "@/components/connections/DatabaseConnectionFieldsForm";
import { EntraAuthFieldsForm } from "@/components/connections/EntraAuthFieldsForm";
import type { ConnectorFormProps } from "@/components/connections/connectorRegistry";
import { POSTGRES_SSL_MODES } from "@/components/connections/types";

export function PostgresqlForm({
  authMethod,
  sqlFields,
  postgresSslMode,
  postgresClientCertFields,
  rdsAwsRegion,
  azureEntra,
  onSqlFieldsChange,
  onPostgresSslModeChange,
  onPostgresClientCertFieldsChange,
  onRdsAwsRegionChange,
  onAzureEntraChange,
}: ConnectorFormProps) {
  return (
    <Stack spacing={1.5}>
      <DatabaseConnectionFieldsForm
        value={sqlFields}
        onChange={onSqlFieldsChange}
        hideCredentials={authMethod.startsWith("entra_") || authMethod === "postgresql_rds_iam"}
        requireCredentials={authMethod === "password" || authMethod === "password_ssl_client_cert"}
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
      {authMethod === "password_ssl_client_cert" && (
        <>
          <TextField
            size="small"
            label="Root CA path (sslrootcert)"
            value={postgresClientCertFields.sslrootcert}
            onChange={(event) =>
              onPostgresClientCertFieldsChange({
                ...postgresClientCertFields,
                sslrootcert: event.target.value,
              })
            }
            required
          />
          <TextField
            size="small"
            label="Client cert path (sslcert)"
            value={postgresClientCertFields.sslcert}
            onChange={(event) =>
              onPostgresClientCertFieldsChange({
                ...postgresClientCertFields,
                sslcert: event.target.value,
              })
            }
            required
          />
          <TextField
            size="small"
            label="Client key path (sslkey)"
            value={postgresClientCertFields.sslkey}
            onChange={(event) =>
              onPostgresClientCertFieldsChange({
                ...postgresClientCertFields,
                sslkey: event.target.value,
              })
            }
            required
          />
        </>
      )}
      {authMethod === "postgresql_rds_iam" && (
        <TextField
          size="small"
          label="AWS region"
          helperText="Region for RDS IAM auth token generation"
          value={rdsAwsRegion}
          onChange={(event) => onRdsAwsRegionChange(event.target.value)}
          required
        />
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
