import Alert from "@mui/material/Alert";
import type { ConnectorFormProps } from "@/components/connections/connectorRegistry";

export function LocalCsvForm(_props: ConnectorFormProps) {
  return (
    <Alert severity="info">
      Local CSV path and upload wiring ships in P1.5. Select another connector for now.
    </Alert>
  );
}
