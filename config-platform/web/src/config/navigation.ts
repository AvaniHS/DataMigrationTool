import CableIcon from "@mui/icons-material/Cable";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import StorageIcon from "@mui/icons-material/Storage";
import FactCheckIcon from "@mui/icons-material/FactCheck";
import type { SvgIconComponent } from "@mui/icons-material";

export type NavModuleStatus = "active" | "coming_soon";

export type NavItem = {
  id: string;
  label: string;
  path: string;
  icon: SvgIconComponent;
  status: NavModuleStatus;
};

export const NAV_ITEMS: NavItem[] = [
  {
    id: "connections",
    label: "Connect",
    path: "/connections",
    icon: CableIcon,
    status: "active",
  },
  {
    id: "configs",
    label: "Configs",
    path: "/migrations",
    icon: AutoAwesomeIcon,
    status: "active",
  },
  {
    id: "run",
    label: "Run",
    path: "/run",
    icon: PlayArrowIcon,
    status: "coming_soon",
  },
  {
    id: "studio",
    label: "Studio",
    path: "/studio",
    icon: StorageIcon,
    status: "coming_soon",
  },
  {
    id: "validation",
    label: "Validate",
    path: "/validation",
    icon: FactCheckIcon,
    status: "coming_soon",
  },
];

export const APP_TITLE = "Data Onboarding Toolkit";
