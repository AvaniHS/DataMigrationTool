import Alert from "@mui/material/Alert";
import { DatabaseConnectionFieldsForm } from "@/components/connections/DatabaseConnectionFieldsForm";
import type { ConnectorFormProps } from "@/components/connections/connectorRegistry";

export function MssqlOnPremForm({ authMethod, sqlFields, onSqlFieldsChange }: ConnectorFormProps) {
  return (
    <>
      {authMethod !== "sql_login" && (
        <Alert severity="warning" sx={{ mb: 1.5 }}>
          Windows auth modes are available in P1.2. Use SQL login for now.
        </Alert>
      )}
      <DatabaseConnectionFieldsForm value={sqlFields} onChange={onSqlFieldsChange} />
    </>
  );
}
