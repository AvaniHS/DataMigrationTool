import { createTheme } from "@mui/material/styles";

export const appTheme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#1565c0",
    },
    secondary: {
      main: "#5c6bc0",
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    body2: { fontSize: "0.8125rem" },
  },
  components: {
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: "1px solid",
          borderColor: "divider",
        },
      },
    },
    MuiButton: {
      defaultProps: { size: "small" },
    },
    MuiTextField: {
      defaultProps: { size: "small", margin: "dense" },
    },
    MuiTable: {
      defaultProps: { size: "small" },
    },
    MuiTableCell: {
      styleOverrides: {
        root: { py: 0.75 },
      },
    },
  },
});
