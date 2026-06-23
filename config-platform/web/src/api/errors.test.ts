import { describe, expect, it } from "vitest";
import { ApiTimeoutError, getApiErrorMessage } from "@/api/errors";

describe("getApiErrorMessage", () => {
  it("returns ApiError message", () => {
    expect(getApiErrorMessage(new ApiTimeoutError(1000))).toContain("timed out");
  });

  it("returns generic message for unknown errors", () => {
    expect(getApiErrorMessage({})).toBe("An unexpected error occurred.");
  });
});
