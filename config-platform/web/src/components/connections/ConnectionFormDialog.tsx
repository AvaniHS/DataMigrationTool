import { useEffect, useMemo, useState } from "react";
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { DatabaseConnectionFieldsForm } from "@/components/connections/DatabaseConnectionFieldsForm";
import { S3ConnectionFieldsForm } from "@/components/connections/S3ConnectionFieldsForm";
import type {
  ConnectionSaveRequest,
  ConnectionType,
  DatabaseConnectionFields,
  S3ConnectionFields,
} from "@/components/connections/types";
import {
  CONNECTION_TYPE_OPTIONS,
  createEmptyDatabaseFields,
  createEmptyS3Fields,
  defaultPortForType,
} from "@/components/connections/types";
import { getApiErrorMessage } from "@/api/errors";

type ConnectionFormDialogProps = {
  open: boolean;
  editRef?: string;
  initialValues?: ConnectionSaveRequest | null;
  onClose: () => void;
  onTest: (body: ConnectionSaveRequest) => Promise<{ message: string; verificationToken: string }>;
  onSave: (body: ConnectionSaveRequest, existingRef?: string) => Promise<void>;
};

type TestState = "idle" | "testing" | "passed" | "failed";

export function ConnectionFormDialog({
  open,
  editRef,
  initialValues,
  onClose,
  onTest,
  onSave,
}: ConnectionFormDialogProps) {
  const [connectionReference, setConnectionReference] = useState("");
  const [connectionType, setConnectionType] = useState<ConnectionType>("MYSQL");
  const [databaseFields, setDatabaseFields] = useState<DatabaseConnectionFields>(
    createEmptyDatabaseFields(defaultPortForType("MYSQL")),
  );
  const [s3Fields, setS3Fields] = useState<S3ConnectionFields>(createEmptyS3Fields());
  const [verificationToken, setVerificationToken] = useState<string | null>(null);
  const [testState, setTestState] = useState<TestState>("idle");
  const [testMessage, setTestMessage] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const isS3 = connectionType === "CSV_S3_BUCKET";
  const isEditing = Boolean(editRef);

  useEffect(() => {
    if (!open) {
      return;
    }
    if (initialValues) {
      setConnectionReference(initialValues.ref);
      setConnectionType(initialValues.type);
      setDatabaseFields(
        initialValues.database ?? createEmptyDatabaseFields(defaultPortForType(initialValues.type)),
      );
      setS3Fields(initialValues.s3 ?? createEmptyS3Fields());
    } else {
      setConnectionReference("");
      setConnectionType("MYSQL");
      setDatabaseFields(createEmptyDatabaseFields(defaultPortForType("MYSQL")));
      setS3Fields(createEmptyS3Fields());
    }
    setVerificationToken(null);
    setTestState("idle");
    setTestMessage(null);
    setSaveError(null);
  }, [open, initialValues]);

  const payload = useMemo<ConnectionSaveRequest>(
    () => ({
      ref: connectionReference,
      type: connectionType,
      database: isS3 ? null : databaseFields,
      s3: isS3 ? s3Fields : null,
      verification_token: verificationToken ?? "",
    }),
    [connectionReference, connectionType, databaseFields, s3Fields, isS3, verificationToken],
  );

  const invalidateTest = () => {
    setVerificationToken(null);
    setTestState("idle");
    setTestMessage(null);
  };

  const handleConnectionTypeChange = (nextType: ConnectionType) => {
    setConnectionType(nextType);
    if (nextType !== "CSV_S3_BUCKET") {
      setDatabaseFields((current) => ({
        ...createEmptyDatabaseFields(defaultPortForType(nextType)),
        host: current.host,
        database: current.database,
        username: current.username,
        password: current.password,
        port: defaultPortForType(nextType),
      }));
    }
    invalidateTest();
  };

  const handleTest = async () => {
    setTestState("testing");
    setTestMessage(null);
    setSaveError(null);
    try {
      const result = await onTest({ ...payload, verification_token: "" });
      setVerificationToken(result.verificationToken);
      setTestState("passed");
      setTestMessage(result.message);
    } catch (error) {
      setTestState("failed");
      setTestMessage(getApiErrorMessage(error));
    }
  };

  const handleSave = async () => {
    if (!verificationToken) {
      setSaveError("Test the connection before saving.");
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      await onSave({ ...payload, verification_token: verificationToken }, editRef);
      onClose();
    } catch (error) {
      setSaveError(getApiErrorMessage(error));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{isEditing ? `Edit connection: ${editRef}` : "Add connection"}</DialogTitle>
      <DialogContent>
        <Stack spacing={1.5} sx={{ mt: 1 }}>
          <TextField
            size="small"
            label="Connection ref"
            helperText="Lowercase slug used in config JSON (e.g. client_crm_mysql)"
            value={connectionReference}
            disabled={isEditing}
            onChange={(event) => {
              setConnectionReference(event.target.value.trim().toLowerCase());
              invalidateTest();
            }}
            required
          />

          <FormControl fullWidth size="small">
            <InputLabel id="connection-type-label">Type</InputLabel>
            <Select
              labelId="connection-type-label"
              label="Type"
              value={connectionType}
              onChange={(event) => handleConnectionTypeChange(event.target.value as ConnectionType)}
            >
              {CONNECTION_TYPE_OPTIONS.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {!isS3 && (
            <DatabaseConnectionFieldsForm
              value={databaseFields}
              onChange={(nextValue) => {
                setDatabaseFields(nextValue);
                invalidateTest();
              }}
            />
          )}

          {isS3 && (
            <S3ConnectionFieldsForm
              value={s3Fields}
              onChange={(nextValue) => {
                setS3Fields(nextValue);
                invalidateTest();
              }}
            />
          )}

          {testMessage && (
            <Alert severity={testState === "passed" ? "success" : "error"}>{testMessage}</Alert>
          )}
          {saveError && <Alert severity="error">{saveError}</Alert>}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button size="small" onClick={onClose}>
          Cancel
        </Button>
        <Button
          size="small"
          onClick={() => void handleTest()}
          disabled={testState === "testing" || !connectionReference}
        >
          {testState === "testing" ? "Testing…" : "Test connection"}
        </Button>
        <Button
          size="small"
          variant="contained"
          onClick={() => void handleSave()}
          disabled={saving || !verificationToken}
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
}
