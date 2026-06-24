import { DatabaseConnectionFieldsForm } from "@/components/connections/DatabaseConnectionFieldsForm";
import type { ConnectorFormProps } from "@/components/connections/connectorRegistry";

export function MysqlForm({ sqlFields, onSqlFieldsChange }: ConnectorFormProps) {
  return <DatabaseConnectionFieldsForm value={sqlFields} onChange={onSqlFieldsChange} />;
}
