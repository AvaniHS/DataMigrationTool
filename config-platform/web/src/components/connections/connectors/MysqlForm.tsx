import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";
import { DatabaseConnectionFieldsForm } from "@/components/connections/DatabaseConnectionFieldsForm";
import type { ConnectorFormProps } from "@/components/connections/connectorRegistry";

export function MysqlForm({ sqlFields, mysqlSslEnabled, onSqlFieldsChange, onMysqlSslEnabledChange }: ConnectorFormProps) {
  return (
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
  );
}
