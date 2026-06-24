import { useRef, useState } from "react";
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { uploadConnectionFile } from "@/api/connections";
import { getApiErrorMessage } from "@/api/errors";
import type { ConnectorFormProps } from "@/components/connections/connectorRegistry";

export function LocalCsvForm({
  authMethod,
  localCsvFields,
  connectionReference,
  onLocalCsvFieldsChange,
}: ConnectorFormProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (file: File | null) => {
    if (!file) {
      return;
    }
    if (!connectionReference) {
      setUploadError("Enter a connection ref before uploading.");
      return;
    }
    setUploading(true);
    setUploadError(null);
    try {
      const response = await uploadConnectionFile(connectionReference, file);
      onLocalCsvFieldsChange({
        ...localCsvFields,
        staging_file_id: response.staging_file_id,
      });
    } catch (error) {
      setUploadError(getApiErrorMessage(error));
    } finally {
      setUploading(false);
    }
  };

  return (
    <Stack spacing={1.5}>
      {authMethod === "local_path" ? (
        <TextField
          size="small"
          label="CSV file path"
          helperText="Absolute path on the API host (must be under CONFIG_API_FILE_ROOTS)"
          value={localCsvFields.file_path}
          onChange={(event) =>
            onLocalCsvFieldsChange({ ...localCsvFields, file_path: event.target.value })
          }
          required
        />
      ) : (
        <Stack spacing={1}>
          <Stack direction="row" spacing={1} alignItems="center">
            <Button
              size="small"
              variant="outlined"
              disabled={uploading || !connectionReference}
              onClick={() => fileInputRef.current?.click()}
            >
              {uploading ? "Uploading…" : "Upload CSV"}
            </Button>
            {localCsvFields.staging_file_id && (
              <Alert severity="success" sx={{ py: 0, flex: 1 }}>
                Staged as {localCsvFields.staging_file_id}
              </Alert>
            )}
          </Stack>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            hidden
            onChange={(event) => void handleUpload(event.target.files?.[0] ?? null)}
          />
          {uploadError && <Alert severity="error">{uploadError}</Alert>}
        </Stack>
      )}

      <Stack direction="row" spacing={1}>
        <TextField
          size="small"
          label="Delimiter"
          value={localCsvFields.parse_options.delimiter}
          inputProps={{ maxLength: 1 }}
          onChange={(event) =>
            onLocalCsvFieldsChange({
              ...localCsvFields,
              parse_options: { ...localCsvFields.parse_options, delimiter: event.target.value },
            })
          }
          sx={{ width: 96 }}
        />
        <TextField
          size="small"
          label="Quote"
          value={localCsvFields.parse_options.quote}
          inputProps={{ maxLength: 1 }}
          onChange={(event) =>
            onLocalCsvFieldsChange({
              ...localCsvFields,
              parse_options: { ...localCsvFields.parse_options, quote: event.target.value },
            })
          }
          sx={{ width: 96 }}
        />
        <TextField
          size="small"
          label="Header row"
          type="number"
          value={localCsvFields.parse_options.header_row}
          onChange={(event) =>
            onLocalCsvFieldsChange({
              ...localCsvFields,
              parse_options: {
                ...localCsvFields.parse_options,
                header_row: Number(event.target.value) || 1,
              },
            })
          }
          sx={{ width: 120 }}
        />
        <TextField
          size="small"
          label="Encoding"
          value={localCsvFields.parse_options.encoding}
          onChange={(event) =>
            onLocalCsvFieldsChange({
              ...localCsvFields,
              parse_options: { ...localCsvFields.parse_options, encoding: event.target.value },
            })
          }
          sx={{ flex: 1 }}
        />
      </Stack>
    </Stack>
  );
}
