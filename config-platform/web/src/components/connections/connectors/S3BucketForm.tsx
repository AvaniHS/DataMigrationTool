import { S3ConnectionFieldsForm } from "@/components/connections/S3ConnectionFieldsForm";
import type { ConnectorFormProps } from "@/components/connections/connectorRegistry";

export function S3BucketForm({ authMethod, s3Fields, onS3FieldsChange }: ConnectorFormProps) {
  return (
    <S3ConnectionFieldsForm
      value={s3Fields}
      onChange={onS3FieldsChange}
      authMethod={authMethod}
    />
  );
}
