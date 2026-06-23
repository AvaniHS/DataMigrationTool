import { ComingSoonPanel } from "@/components/shared/ComingSoonPanel";
import { PageHeader } from "@/components/shared/PageHeader";

export function ConnectionsView() {
  return (
    <>
      <PageHeader title="Connect" />
      <ComingSoonPanel
        title="Connections manager"
        description="Add, test, and save MYSQL, MSSQL, POSTGRESQL, and CSV_S3_BUCKET connections. Full workflow ships in P1."
      />
    </>
  );
}
