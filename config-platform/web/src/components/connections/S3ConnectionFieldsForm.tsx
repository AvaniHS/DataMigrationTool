import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import type { S3BucketFields } from "@/components/connections/types";

type S3ConnectionFieldsFormProps = {
  value: S3BucketFields;
  onChange: (nextValue: S3BucketFields) => void;
  showAccessKeys?: boolean;
};

export function S3ConnectionFieldsForm({
  value,
  onChange,
  showAccessKeys = true,
}: S3ConnectionFieldsFormProps) {
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
    </Stack>
  );
}
