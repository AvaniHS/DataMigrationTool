import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";

type ErrorAlertWithRetryProps = {
  message: string;
  onRetry?: () => void;
};

export function ErrorAlertWithRetry({ message, onRetry }: ErrorAlertWithRetryProps) {
  return (
    <Alert
      severity="error"
      action={
        onRetry ? (
          <Button color="inherit" size="small" onClick={onRetry}>
            Retry
          </Button>
        ) : undefined
      }
    >
      {message}
    </Alert>
  );
}
