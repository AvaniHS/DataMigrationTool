import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { Blueprint } from "@/components/migrations/types";
import { collectSourceAliases } from "./blueprintHelpers";

type StepBlueprintReviewProps = {
  blueprint: Blueprint;
};

export function StepBlueprintReview({ blueprint }: StepBlueprintReviewProps) {
  const root = blueprint.sources.root_table;
  const aliases = collectSourceAliases(blueprint);

  return (
    <Stack spacing={1.5}>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        <Chip size="small" label={`Target: ${blueprint.target.schema}.${blueprint.target.table_name || "—"}`} />
        <Chip size="small" label={`Conflict: ${blueprint.target.on_conflict}`} />
        <Chip size="small" label={`Mappings: ${blueprint.mappings.length}`} />
        <Chip size="small" label={`Joins: ${blueprint.sources.joins.length}`} />
        <Chip size="small" label={`Derivations: ${blueprint.derivations.length}`} />
      </Stack>

      <Box>
        <Typography variant="subtitle2">Sources</Typography>
        <Typography variant="body2" color="text.secondary">
          Root: {root.connection_ref || "—"} · alias {root.alias}
          {root.file_name
            ? ` · file ${root.file_name}`
            : ` · ${root.schema}.${root.table_name || "—"}`}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Aliases: {aliases.length > 0 ? aliases.join(", ") : "none"}
        </Typography>
        {blueprint.sources.joins.map((join, index) => (
          <Typography key={`review-join-${index}`} variant="body2" color="text.secondary">
            Join {index + 1}: {join.join_type} {join.alias} ({join.connection_ref})
            {join.file_name ? ` file ${join.file_name}` : ` ${join.schema}.${join.table_name}`}
            {" · "}
            {join.conditions.length} condition(s)
          </Typography>
        ))}
      </Box>

      <Divider />

      <Box>
        <Typography variant="subtitle2">Target</Typography>
        <Typography variant="body2" color="text.secondary">
          {blueprint.target.connection_ref || "—"} → {blueprint.target.schema}.
          {blueprint.target.table_name || "—"}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Primary keys: {blueprint.target.primary_keys.join(", ") || "none"}
        </Typography>
        {blueprint.target.unprocessed_table && (
          <Typography variant="body2" color="text.secondary">
            Unprocessed table: {blueprint.target.unprocessed_table}
          </Typography>
        )}
        {blueprint.target.audit_table && (
          <Typography variant="body2" color="text.secondary">
            Audit table: {blueprint.target.audit_table}
          </Typography>
        )}
      </Box>

      <Divider />

      <Box>
        <Typography variant="subtitle2">Filters & chunking</Typography>
        <Typography variant="body2" color="text.secondary">
          Pre-filters: {blueprint.pre_filters.length} · Post-filters: {blueprint.post_filters.length}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Chunking:{" "}
          {blueprint.chunking_strategy.is_enabled
            ? `${blueprint.chunking_strategy.chunk_by_column} / ${blueprint.chunking_strategy.chunk_size}`
            : "disabled"}
        </Typography>
      </Box>

      <Paper
        variant="outlined"
        sx={{
          p: 1.5,
          maxHeight: 280,
          overflow: "auto",
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
          fontSize: 12,
          whiteSpace: "pre-wrap",
        }}
      >
        {JSON.stringify(blueprint, null, 2)}
      </Paper>
    </Stack>
  );
}
