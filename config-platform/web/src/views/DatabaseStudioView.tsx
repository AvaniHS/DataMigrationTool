import { ComingSoonPanel } from "@/components/shared/ComingSoonPanel";
import { PageHeader } from "@/components/shared/PageHeader";

export function DatabaseStudioView() {
  return (
    <>
      <PageHeader title="Studio" />
      <ComingSoonPanel
        title="Database Studio"
        description="SQL scratchpad, schema exploration, and ad-hoc queries. Slots into the same shell without layout rewrite."
      />
    </>
  );
}
