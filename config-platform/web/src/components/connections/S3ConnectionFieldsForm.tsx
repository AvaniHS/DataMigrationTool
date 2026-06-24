import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import type { S3BucketFields } from "@/components/connections/types";

type S3ConnectionFieldsFormProps = {
  value: S3BucketFields;
  onChange: (nextValue: S3BucketFields) => void;
};

export function S3ConnectionFieldsForm({ value, onChange }: S3ConnectionFieldsFormProps) {
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
    </Stack>
  );
}
