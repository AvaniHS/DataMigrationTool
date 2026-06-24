import { useEffect, useRef } from "react";
import TextField from "@mui/material/TextField";
import type { TextFieldProps } from "@mui/material/TextField";

type SqlCodeEditorProps = Omit<TextFieldProps, "multiline" | "onChange"> & {
  value: string;
  onChange: (value: string) => void;
  minRows?: number;
  onDebouncedChange?: (value: string) => void;
  debounceMs?: number;
};

export function SqlCodeEditor({
  value,
  onChange,
  minRows = 3,
  onDebouncedChange,
  debounceMs = 500,
  ...textFieldProps
}: SqlCodeEditorProps) {
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!onDebouncedChange) {
      return;
    }
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => onDebouncedChange(value), debounceMs);
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [value, onDebouncedChange, debounceMs]);

  return (
    <TextField
      {...textFieldProps}
      fullWidth
      multiline
      minRows={minRows}
      size="small"
      value={value}
      onChange={(event) => onChange(event.target.value)}
      slotProps={{
        input: {
          sx: {
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
            fontSize: 13,
          },
        },
      }}
    />
  );
}
