import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import { blueprintLabel, type Blueprint } from "@/components/migrations/types";

type BlueprintListProps = {
  blueprints: Blueprint[];
  selectedSequenceOrder: number | null;
  busy?: boolean;
  onAdd: () => void;
  onSelect: (sequenceOrder: number) => void;
  onDuplicate: (sequenceOrder: number) => void;
  onDelete: (sequenceOrder: number) => void;
  onMoveUp: (sequenceOrder: number) => void;
  onMoveDown: (sequenceOrder: number) => void;
};

export function BlueprintList({
  blueprints,
  selectedSequenceOrder,
  busy = false,
  onAdd,
  onSelect,
  onDuplicate,
  onDelete,
  onMoveUp,
  onMoveDown,
}: BlueprintListProps) {
  const ordered = [...blueprints].sort((left, right) => left.sequence_order - right.sequence_order);

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
        <Typography variant="subtitle2">Blueprints (M2)</Typography>
        <Button size="small" variant="contained" onClick={onAdd} disabled={busy}>
          Add blueprint
        </Button>
      </Stack>

      {ordered.length === 0 ? (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="body2" color="text.secondary">
            No blueprints yet. Add one to start the per-blueprint wizard.
          </Typography>
        </Paper>
      ) : (
        <Paper variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell width={56}>#</TableCell>
                <TableCell>Label</TableCell>
                <TableCell width={180} align="right">
                  Actions
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {ordered.map((blueprint, index) => {
                const isSelected = blueprint.sequence_order === selectedSequenceOrder;
                return (
                  <TableRow
                    key={blueprint.sequence_order}
                    hover
                    selected={isSelected}
                    onClick={() => onSelect(blueprint.sequence_order)}
                    sx={{ cursor: "pointer" }}
                  >
                    <TableCell>{blueprint.sequence_order}</TableCell>
                    <TableCell>{blueprintLabel(blueprint)}</TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        aria-label="Move up"
                        disabled={busy || index === 0}
                        onClick={(event) => {
                          event.stopPropagation();
                          onMoveUp(blueprint.sequence_order);
                        }}
                      >
                        <ArrowUpwardIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        aria-label="Move down"
                        disabled={busy || index === ordered.length - 1}
                        onClick={(event) => {
                          event.stopPropagation();
                          onMoveDown(blueprint.sequence_order);
                        }}
                      >
                        <ArrowDownwardIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        aria-label="Duplicate"
                        disabled={busy}
                        onClick={(event) => {
                          event.stopPropagation();
                          onDuplicate(blueprint.sequence_order);
                        }}
                      >
                        <ContentCopyIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        aria-label="Delete"
                        disabled={busy}
                        onClick={(event) => {
                          event.stopPropagation();
                          onDelete(blueprint.sequence_order);
                        }}
                      >
                        <DeleteOutlineIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </Paper>
      )}
    </Box>
  );
}
