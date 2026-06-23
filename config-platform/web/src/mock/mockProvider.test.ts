import { describe, expect, it } from "vitest";
import { isMockDataEnabled } from "@/mock/mockProvider";

describe("isMockDataEnabled", () => {
  it("returns true when VITE_USE_MOCK_DATA is true", () => {
    expect(isMockDataEnabled()).toBe(true);
  });
});
