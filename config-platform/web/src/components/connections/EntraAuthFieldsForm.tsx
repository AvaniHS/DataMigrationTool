import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import type { AzureEntraFields } from "@/components/connections/types";

type EntraAuthFieldsFormProps = {
  authMethod: string;
  value: AzureEntraFields;
  onChange: (nextValue: AzureEntraFields) => void;
  showEntraUser?: boolean;
};

export function EntraAuthFieldsForm({
  authMethod,
  value,
  onChange,
  showEntraUser = true,
}: EntraAuthFieldsFormProps) {
  const update = (patch: Partial<AzureEntraFields>) => {
    onChange({ ...value, ...patch });
  };

  if (authMethod === "entra_service_principal") {
    return (
      <Stack spacing={1.5}>
        <TextField
          size="small"
          label="Tenant ID"
          value={value.tenant_id}
          onChange={(event) => update({ tenant_id: event.target.value })}
          required
        />
        <TextField
          size="small"
          label="Client ID"
          value={value.client_id}
          onChange={(event) => update({ client_id: event.target.value })}
          required
        />
        <TextField
          size="small"
          label="Client secret"
          type="password"
          value={value.client_secret}
          onChange={(event) => update({ client_secret: event.target.value })}
          required
        />
        {showEntraUser && (
          <TextField
            size="small"
            label="Entra user"
            helperText="Azure AD user name configured on the database (e.g. user@domain.com)"
            value={value.entra_user}
            onChange={(event) => update({ entra_user: event.target.value })}
            required
          />
        )}
      </Stack>
    );
  }

  if (authMethod === "entra_password") {
    return (
      <Stack spacing={1.5}>
        <TextField
          size="small"
          label="Tenant ID"
          value={value.tenant_id}
          onChange={(event) => update({ tenant_id: event.target.value })}
          required
        />
        <TextField
          size="small"
          label="Client ID"
          helperText="Public client app registration ID for the user/password token flow"
          value={value.client_id}
          onChange={(event) => update({ client_id: event.target.value })}
          required
        />
        <TextField
          size="small"
          label="Entra user"
          value={value.entra_user}
          onChange={(event) => update({ entra_user: event.target.value })}
          required
        />
        <TextField
          size="small"
          label="Entra password"
          type="password"
          value={value.entra_password}
          onChange={(event) => update({ entra_password: event.target.value })}
          required
        />
      </Stack>
    );
  }

  if (authMethod === "entra_managed_identity") {
    return (
      <Stack spacing={1.5}>
        {showEntraUser && (
          <TextField
            size="small"
            label="Entra user"
            helperText="Azure AD user name configured on the database"
            value={value.entra_user}
            onChange={(event) => update({ entra_user: event.target.value })}
            required
          />
        )}
        <TextField
          size="small"
          label="Managed identity client ID"
          helperText="Optional — leave blank for the system-assigned identity"
          value={value.managed_identity_client_id}
          onChange={(event) => update({ managed_identity_client_id: event.target.value })}
        />
      </Stack>
    );
  }

  return null;
}
