import { describe, expect, it } from "vitest";
import { buildDraftKey, readLocalDraft, writeLocalDraft } from "@/storage/localDraft";

describe("localDraft", () => {
  it("builds namespaced storage keys", () => {
    expect(buildDraftKey("wizard-step:demo")).toBe("migration-toolkit:wizard-step:demo");
  });

  it("round-trips JSON values", () => {
    const key = buildDraftKey("test-roundtrip");
    writeLocalDraft(key, { step: 2 });
    expect(readLocalDraft<{ step: number }>(key)).toEqual({ step: 2 });
    localStorage.removeItem(key);
  });

  it("returns null for invalid JSON", () => {
    const key = buildDraftKey("test-invalid");
    localStorage.setItem(key, "{bad");
    expect(readLocalDraft(key)).toBeNull();
    localStorage.removeItem(key);
  });
});
