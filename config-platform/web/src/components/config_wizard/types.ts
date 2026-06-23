export type BlueprintWizardStepId = "sources" | "target" | "mappings" | "filters" | "review";

export type BlueprintWizardStep = {
  id: BlueprintWizardStepId;
  label: string;
  shortLabel: string;
  description: string;
};

export const BLUEPRINT_WIZARD_STEPS: BlueprintWizardStep[] = [
  {
    id: "sources",
    label: "Sources & joins",
    shortLabel: "Sources",
    description: "Schema tree, root table, and join graph (B1).",
  },
  {
    id: "target",
    label: "Target & conflict",
    shortLabel: "Target",
    description: "Target table, primary keys, and on_conflict strategy (B2).",
  },
  {
    id: "mappings",
    label: "Mappings & derivations",
    shortLabel: "Mappings",
    description: "Derivations drawer and per-column mapping grid (B3).",
  },
  {
    id: "filters",
    label: "Filters & chunking",
    shortLabel: "Filters",
    description: "Pre/post filters and optional chunking (B4).",
  },
  {
    id: "review",
    label: "Review",
    shortLabel: "Review",
    description: "Blueprint summary and step-level checks (B5).",
  },
];
