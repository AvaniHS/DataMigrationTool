import { NavLink, Outlet, useLocation } from "react-router-dom";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Drawer from "@mui/material/Drawer";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import { APP_TITLE, NAV_ITEMS } from "@/config/navigation";
import { useApiHealth } from "@/hooks/useApiHealth";

const DRAWER_WIDTH = 260;

export function AppLayout() {
  const location = useLocation();
  const apiStatus = useApiHealth();

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: DRAWER_WIDTH, boxSizing: "border-box" },
        }}
      >
        <Toolbar>
          <Typography variant="subtitle1" fontWeight={700} noWrap>
            {APP_TITLE}
          </Typography>
        </Toolbar>
        <List component="nav" aria-label="Main navigation" dense>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const selected =
              location.pathname === item.path ||
              (item.path !== "/" && location.pathname.startsWith(item.path));

            return (
              <ListItemButton
                key={item.id}
                component={NavLink}
                to={item.path}
                selected={selected}
                dense
              >
                <ListItemIcon>
                  <Icon fontSize="small" />
                </ListItemIcon>
                <ListItemText primary={item.label} />
                {item.status === "active" ? (
                  <Chip label="v1" size="small" color="primary" variant="outlined" />
                ) : (
                  <Chip label="soon" size="small" variant="outlined" />
                )}
              </ListItemButton>
            );
          })}
        </List>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 2, minWidth: 0 }}>
        <Box sx={{ mb: 1.5, display: "flex", justifyContent: "flex-end" }}>
          <Chip
            size="small"
            label={
              apiStatus === "checking"
                ? "API: checking…"
                : apiStatus === "ok"
                  ? "API: connected"
                  : "API: offline"
            }
            color={apiStatus === "ok" ? "success" : apiStatus === "offline" ? "warning" : "default"}
            variant="outlined"
          />
        </Box>
        <Outlet />
      </Box>
    </Box>
  );
}
