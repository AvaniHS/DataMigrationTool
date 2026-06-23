import { ComingSoonPanel } from "@/components/shared/ComingSoonPanel";
import { PageHeader } from "@/components/shared/PageHeader";

export function MigrationRunnerView() {
  return (
    <>
      <PageHeader title="Run" />
      <ComingSoonPanel
        title="Job Runner"
        description="Execute generated or uploaded SQL against the target. This module will deep-link to the migrator product."
        futureOwner="migrator"
      />
    </>
  );
}
