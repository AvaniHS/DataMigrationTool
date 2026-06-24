import FormControlLabel from "@mui/material/FormControlLabel";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import TextField from "@mui/material/TextField";
import type { SqlDatabaseFields } from "@/components/connections/types";

type DatabaseConnectionFieldsFormProps = {
  value: SqlDatabaseFields;
  onChange: (nextValue: SqlDatabaseFields) => void;
  hideCredentials?: boolean;
  requireCredentials?: boolean;
};

export function DatabaseConnectionFieldsForm({
  value,
  onChange,
  hideCredentials = false,
  requireCredentials = true,
}: DatabaseConnectionFieldsFormProps) {
  const update = (patch: Partial<SqlDatabaseFields>) => {
    onChange({ ...value, ...patch });
  };

  return (
    <Stack spacing={1.5}>
      <TextField
        size="small"
        label="Host"
        value={value.host}
        onChange={(event) => update({ host: event.target.value })}
        required
      />
      <TextField
        size="small"
        label="Port"
        type="number"
        value={value.port}
        onChange={(event) => update({ port: Number(event.target.value) })}
        required
      />
      <TextField
        size="small"
        label="Database"
        value={value.database}
        onChange={(event) => update({ database: event.target.value })}
        required
      />
      {!hideCredentials && (
        <>
          <TextField
            size="small"
            label="Username"
            value={value.username}
            onChange={(event) => update({ username: event.target.value })}
            required={requireCredentials}
          />
          <TextField
            size="small"
            label="Password"
            type="password"
            value={value.password}
            onChange={(event) => update({ password: event.target.value })}
            required={requireCredentials}
          />
        </>
      )}
      <FormControlLabel
        control={
          <Switch
            size="small"
            checked={value.use_advanced_string}
            onChange={(event) =>
              update({
                use_advanced_string: event.target.checked,
                connection_string: event.target.checked ? value.connection_string ?? "" : null,
              })
            }
          />
        }
        label="Advanced: edit connection string"
      />
      {value.use_advanced_string && (
        <TextField
          size="small"
          label="Connection string"
          value={value.connection_string ?? ""}
          onChange={(event) => update({ connection_string: event.target.value })}
          multiline
          minRows={2}
          required
        />
      )}
    </Stack>
  );
}
