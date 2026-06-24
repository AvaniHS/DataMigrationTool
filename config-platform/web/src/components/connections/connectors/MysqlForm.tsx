import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";
import Stack from "@mui/material/Stack";
import { DatabaseConnectionFieldsForm } from "@/components/connections/DatabaseConnectionFieldsForm";
import { EntraAuthFieldsForm } from "@/components/connections/EntraAuthFieldsForm";
import type { ConnectorFormProps } from "@/components/connections/connectorRegistry";

export function MysqlForm({
  authMethod,
  sqlFields,
  mysqlSslEnabled,
  azureEntra,
  onSqlFieldsChange,
  onMysqlSslEnabledChange,
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
