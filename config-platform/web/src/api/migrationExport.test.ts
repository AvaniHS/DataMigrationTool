import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { downloadMigrationExport } from "./migrationExport";

describe("migrationExport", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        blob: async () => new Blob(['{"migration_id":"mig_test"}'], { type: "application/json" }),
      }),
    );
    vi.stubGlobal("URL", {
      createObjectURL: vi.fn(() => "blob:export"),
      revokeObjectURL: vi.fn(),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("downloads migration export via attachment endpoint", async () => {
    const click = vi.fn();
    const remove = vi.fn();
    const link = { href: "", download: "", click, remove } as unknown as HTMLAnchorElement;
    const createElement = vi.spyOn(document, "createElement").mockReturnValue(link);
    const appendChild = vi.spyOn(document.body, "appendChild").mockImplementation(() => link);

    await downloadMigrationExport("mig_test");

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/migrations/mig_test/export?download=true"),
      expect.objectContaining({ headers: { Accept: "application/json" } }),
    );
    expect(link.download).toBe("mig_test.json");
    expect(click).toHaveBeenCalled();
    createElement.mockRestore();
    appendChild.mockRestore();
  });
});
