import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";

type ComingSoonPanelProps = {
  title: string;
  description: string;
  futureOwner?: string;
};

export function ComingSoonPanel({ title, description, futureOwner }: ComingSoonPanelProps) {
  return (
    <Paper variant="outlined" sx={{ p: 4, maxWidth: 640 }}>
      <Typography variant="h5" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        {description}
      </Typography>
      {futureOwner && (
        <Typography variant="body2" color="text.secondary">
          Planned owner: {futureOwner}
        </Typography>
      )}
      <Box
        sx={{
          mt: 3,
          px: 2,
          py: 1,
          display: "inline-block",
          bgcolor: "action.selected",
          borderRadius: 1,
          typography: "caption",
        }}
      >
        Coming soon — route registered in P0
      </Box>
    </Paper>
  );
}
