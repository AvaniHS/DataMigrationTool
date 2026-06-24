import { describe, expect, it } from "vitest";
import { buildDraftKey, readLocalDraft, writeLocalDraft } from "@/storage/localDraft";
import { buildWizardStepDraftKey } from "@/hooks/useWizardStepIndex";

describe("buildWizardStepDraftKey", () => {
  it("scopes wizard step drafts per migration and blueprint sequence", () => {
    const migrationId = "mig_test_2026";
    const keyBlueprint1 = buildWizardStepDraftKey(migrationId, 1);
    const keyBlueprint2 = buildWizardStepDraftKey(migrationId, 2);

    expect(keyBlueprint1).toBe(buildDraftKey("wizard-step:mig_test_2026:1"));
    expect(keyBlueprint2).toBe(buildDraftKey("wizard-step:mig_test_2026:2"));
    expect(keyBlueprint1).not.toBe(keyBlueprint2);

    writeLocalDraft(keyBlueprint1, 3);
    writeLocalDraft(keyBlueprint2, 1);

    expect(readLocalDraft<number>(keyBlueprint1)).toBe(3);
    expect(readLocalDraft<number>(keyBlueprint2)).toBe(1);

    localStorage.removeItem(keyBlueprint1);
    localStorage.removeItem(keyBlueprint2);
  });
});
