import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import FormControlLabel from "@mui/material/FormControlLabel";
import IconButton from "@mui/material/IconButton";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import type { Blueprint } from "@/components/migrations/types";
import { SqlCodeEditor } from "@/components/shared/SqlCodeEditor";
import { collectSourceAliases } from "./blueprintHelpers";

type StepFiltersChunkingProps = {
  blueprint: Blueprint;
  onChange: (blueprint: Blueprint) => void;
};

export function StepFiltersChunking({ blueprint, onChange }: StepFiltersChunkingProps) {
  const aliases = collectSourceAliases(blueprint);
  const chunking = blueprint.chunking_strategy;

  const updateChunking = (patch: Partial<Blueprint["chunking_strategy"]>) => {
    onChange({
      ...blueprint,
      chunking_strategy: { ...chunking, ...patch },
    });
  };

  const updateFilterList = (field: "pre_filters" | "post_filters", values: string[]) => {
    onChange({ ...blueprint, [field]: values });
  };

  return (
    <Stack spacing={2}>
      <FilterListEditor
        title="Pre-filters"
        helperText="SQL predicates applied before the extract query runs."
        values={blueprint.pre_filters}
        onChange={(values) => updateFilterList("pre_filters", values)}
      />
      <FilterListEditor
        title="Post-filters"
        helperText="SQL predicates applied after joins/derivations."
        values={blueprint.post_filters}
        onChange={(values) => updateFilterList("post_filters", values)}
      />

      <Box>
        <FormControlLabel
          control={
            <Switch
              size="small"
              checked={chunking.is_enabled}
              onChange={(event) =>
                updateChunking({
                  is_enabled: event.target.checked,
                  chunk_by_column: event.target.checked ? chunking.chunk_by_column : null,
                  chunk_size: event.target.checked ? chunking.chunk_size : null,
                })
              }
            />
          }
          label="Enable chunking"
        />
        {chunking.is_enabled && (
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ mt: 1 }}>
            <TextField
              size="small"
              label="Chunk by column"
              value={chunking.chunk_by_column ?? ""}
              onChange={(event) => updateChunking({ chunk_by_column: event.target.value || null })}
              helperText={
                aliases.length > 0
                  ? `Use alias-qualified columns, e.g. ${aliases[0]}.id`
                  : "Alias-qualified column recommended"
              }
              sx={{ flex: 1 }}
            />
            <TextField
              size="small"
              label="Chunk size"
              type="number"
              value={chunking.chunk_size ?? ""}
              onChange={(event) => {
                const parsed = Number(event.target.value);
                updateChunking({
                  chunk_size: Number.isFinite(parsed) && parsed > 0 ? parsed : null,
                });
              }}
              sx={{ width: 160 }}
            />
          </Stack>
        )}
      </Box>
    </Stack>
  );
}

type FilterListEditorProps = {
  title: string;
  helperText: string;
  values: string[];
  onChange: (values: string[]) => void;
};

function FilterListEditor({ title, helperText, values, onChange }: FilterListEditorProps) {
  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.5 }}>
        <Typography variant="subtitle2">{title}</Typography>
        <Button
          size="small"
          startIcon={<AddIcon />}
          onClick={() => onChange([...values, ""])}
        >
          Add
        </Button>
      </Stack>
      <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 1 }}>
        {helperText}
      </Typography>
      {values.length === 0 && (
        <Typography variant="body2" color="text.secondary">
          No {title.toLowerCase()} configured.
        </Typography>
      )}
      <Stack spacing={1}>
        {values.map((value, index) => (
          <Stack key={`${title}-${index}`} direction="row" spacing={1} alignItems="flex-start">
            <SqlCodeEditor
              label={`${title} ${index + 1}`}
              value={value}
              onChange={(nextValue) =>
                onChange(values.map((item, itemIndex) => (itemIndex === index ? nextValue : item)))
              }
              minRows={2}
              sx={{ flex: 1 }}
            />
            <IconButton
              size="small"
              aria-label={`Delete ${title} ${index + 1}`}
              onClick={() => onChange(values.filter((_, itemIndex) => itemIndex !== index))}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Stack>
        ))}
      </Stack>
    </Box>
  );
}
