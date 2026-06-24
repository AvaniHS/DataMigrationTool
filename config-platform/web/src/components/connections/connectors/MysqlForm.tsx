import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { DatabaseConnectionFieldsForm } from "@/components/connections/DatabaseConnectionFieldsForm";
import { EntraAuthFieldsForm } from "@/components/connections/EntraAuthFieldsForm";
import type { ConnectorFormProps } from "@/components/connections/connectorRegistry";
import { MYSQL_SSL_MODES } from "@/components/connections/types";

export function MysqlForm({
  authMethod,
  sqlFields,
  mysqlSslEnabled,
  mysqlSslFields,
  rdsAwsRegion,
  azureEntra,
  onSqlFieldsChange,
  onMysqlSslEnabledChange,
  onMysqlSslFieldsChange,
  onRdsAwsRegionChange,
  onAzureEntraChange,
}: ConnectorFormProps) {
  return (
    <Stack spacing={1.5}>
      {authMethod === "password" && (
        <>
          <DatabaseConnectionFieldsForm value={sqlFields} onChange={onSqlFieldsChange} />
          <FormControlLabel
            control={
              <Checkbox
                size="small"
                checked={mysqlSslEnabled}
                onChange={(event) => onMysqlSslEnabledChange(event.target.checked)}
              />
            }
            label="Use SSL/TLS"
          />
        </>
      )}
      {authMethod === "password_ssl" && (
        <>
          <DatabaseConnectionFieldsForm value={sqlFields} onChange={onSqlFieldsChange} />
          <FormControl fullWidth size="small">
            <InputLabel id="mysql-ssl-mode-label">SSL mode</InputLabel>
            <Select
              labelId="mysql-ssl-mode-label"
              label="SSL mode"
              value={mysqlSslFields.ssl_mode}
              onChange={(event) =>
                onMysqlSslFieldsChange({
                  ...mysqlSslFields,
                  ssl_mode: event.target.value as typeof mysqlSslFields.ssl_mode,
                })
              }
            >
              {MYSQL_SSL_MODES.map((mode) => (
                <MenuItem key={mode} value={mode}>
                  {mode}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            size="small"
            label="CA certificate path (optional)"
            value={mysqlSslFields.ssl_ca_path}
            onChange={(event) =>
              onMysqlSslFieldsChange({ ...mysqlSslFields, ssl_ca_path: event.target.value })
            }
          />
        </>
      )}
      {authMethod === "mysql_rds_iam" && (
        <>
          <DatabaseConnectionFieldsForm
            value={sqlFields}
            onChange={onSqlFieldsChange}
            hideCredentials
            requireCredentials={false}
          />
          <TextField
            size="small"
            label="AWS region"
            helperText="Region for RDS IAM auth token generation"
            value={rdsAwsRegion}
            onChange={(event) => onRdsAwsRegionChange(event.target.value)}
            required
          />
        </>
      )}
      {authMethod.startsWith("entra_") && (
        <>
          <DatabaseConnectionFieldsForm
            value={sqlFields}
            onChange={onSqlFieldsChange}
            hideCredentials
            requireCredentials={false}
          />
          <EntraAuthFieldsForm
            authMethod={authMethod}
            value={azureEntra}
            onChange={onAzureEntraChange}
          />
        </>
      )}
    </Stack>
  );
}
