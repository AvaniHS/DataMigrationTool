import Alert from "@mui/material/Alert";
import { DatabaseConnectionFieldsForm } from "@/components/connections/DatabaseConnectionFieldsForm";
import type { ConnectorFormProps } from "@/components/connections/connectorRegistry";

export function PostgresqlForm({ sqlFields, onSqlFieldsChange }: ConnectorFormProps) {
  return (
    <>
      <Alert severity="info" sx={{ mb: 1.5 }}>
        Full <code>sslmode</code> controls ship in P1.2. Default is <code>prefer</code>.
      </Alert>
      <DatabaseConnectionFieldsForm value={sqlFields} onChange={onSqlFieldsChange} />
    </>
  );
}
