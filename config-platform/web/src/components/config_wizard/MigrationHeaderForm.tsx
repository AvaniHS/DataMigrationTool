import { useEffect, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import type { MigrationHeaderValues } from "@/components/migrations/types";

type MigrationHeaderFormProps = {
  values: MigrationHeaderValues;
  readOnlyId?: boolean;
  saving?: boolean;
  onChange: (values: MigrationHeaderValues) => void;
};

export function MigrationHeaderForm({
  values,
  readOnlyId = true,
  saving = false,
  onChange,
}: MigrationHeaderFormProps) {
  const [localValues, setLocalValues] = useState(values);

  useEffect(() => {
    setLocalValues(values);
  }, [values]);

  const updateField = (field: keyof MigrationHeaderValues, value: string) => {
    const next = { ...localValues, [field]: value };
    setLocalValues(next);
    onChange(next);
  };

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        Migration identity (M0)
      </Typography>
      <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} useFlexGap flexWrap="wrap">
        <TextField
          size="small"
          label="migration_id"
          value={localValues.migration_id}
          disabled={readOnlyId || saving}
          onChange={(event) => updateField("migration_id", event.target.value)}
          sx={{ minWidth: 240, flex: 1 }}
        />
        <TextField
          size="small"
          label="client_id"
          value={localValues.client_id}
          disabled={saving}
          onChange={(event) => updateField("client_id", event.target.value)}
          sx={{ minWidth: 200, flex: 1 }}
        />
        <TextField
          size="small"
          label="version"
          value={localValues.version}
          disabled={saving}
          onChange={(event) => updateField("version", event.target.value)}
          sx={{ minWidth: 120, flex: 0.6 }}
        />
        <TextField
          size="small"
          label="output_format"
          value="SQL"
          disabled
          sx={{ minWidth: 100, flex: 0.5 }}
        />
        <TextField
          size="small"
          label="compile dialect"
          value="MySQL"
          disabled
          sx={{ minWidth: 120, flex: 0.6 }}
        />
      </Stack>
      <Alert severity="info" sx={{ mt: 1.5, py: 0 }}>
        output_format and compile dialect are fixed for v1.
      </Alert>
    </Box>
  );
}
