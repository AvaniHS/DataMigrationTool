import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import type { S3BucketFields } from "@/components/connections/types";

type S3ConnectionFieldsFormProps = {
  value: S3BucketFields;
  onChange: (nextValue: S3BucketFields) => void;
  authMethod: string;
};

export function S3ConnectionFieldsForm({
  value,
  onChange,
  authMethod,
}: S3ConnectionFieldsFormProps) {
  const showAccessKeys = authMethod === "access_key" || authMethod === "session_token";
  const showSessionToken = authMethod === "session_token";
  const showAssumeRole = authMethod === "assume_role";

  return (
    <Stack spacing={1.5}>
      <TextField
        size="small"
        label="S3 bucket URI"
        helperText="Example: s3://bucket-name/path/prefix/"
        value={value.s3_bucket_uri}
        onChange={(event) => onChange({ ...value, s3_bucket_uri: event.target.value })}
        required
      />
      <TextField
        size="small"
        label="AWS region"
        value={value.aws_region}
        onChange={(event) => onChange({ ...value, aws_region: event.target.value })}
        required
      />
      {showAccessKeys && (
        <>
          <TextField
            size="small"
            label="Access key ID"
            value={value.access_key_id}
            onChange={(event) => onChange({ ...value, access_key_id: event.target.value })}
            required
          />
          <TextField
            size="small"
            label="Secret access key"
            type="password"
            value={value.secret_access_key}
            onChange={(event) => onChange({ ...value, secret_access_key: event.target.value })}
            required
          />
        </>
      )}
      {showSessionToken && (
        <TextField
          size="small"
          label="Session token"
          type="password"
          value={value.session_token}
          onChange={(event) => onChange({ ...value, session_token: event.target.value })}
          required
        />
      )}
      {showAssumeRole && (
        <>
          <TextField
            size="small"
            label="Role ARN"
            value={value.role_arn}
            onChange={(event) => onChange({ ...value, role_arn: event.target.value })}
            required
          />
          <TextField
            size="small"
            label="External ID (optional)"
            value={value.external_id}
            onChange={(event) => onChange({ ...value, external_id: event.target.value })}
          />
        </>
      )}
      {authMethod === "instance_profile" && (
        <TextField
          size="small"
          label="Auth"
          value="Uses IAM role / instance profile on API host"
          disabled
        />
      )}
    </Stack>
  );
}
