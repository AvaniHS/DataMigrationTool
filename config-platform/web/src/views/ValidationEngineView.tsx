import { ComingSoonPanel } from "@/components/shared/ComingSoonPanel";
import { PageHeader } from "@/components/shared/PageHeader";

export function ValidationEngineView() {
  return (
    <>
      <PageHeader title="Validate" />
      <ComingSoonPanel
        title="Validation Engine"
        description="Post-migration checksums, row counts, and audit reports after a migrator run."
        futureOwner="migrator"
      />
    </>
  );
}
