import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";

type PageHeaderProps = {
  title: string;
  description?: ReactNode;
  children?: ReactNode;
};

export function PageHeader({ title, description, children }: PageHeaderProps) {
  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h4" gutterBottom={Boolean(description || children)}>
        {title}
      </Typography>
      {description && (
        <Typography variant="body1" color="text.secondary" component="div">
          {description}
        </Typography>
      )}
      {children && <Box sx={{ mt: description ? 2 : 0 }}>{children}</Box>}
    </Box>
  );
}
