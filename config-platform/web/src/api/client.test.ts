import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/api/logger", () => ({
  apiLogger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
  logClientError: vi.fn(),
}));

describe("apiFetch", () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.resetModules();
  });

  it("throws api_timeout when the request is aborted", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: string, init?: RequestInit) =>
        new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => {
            reject(new DOMException("The operation was aborted.", "AbortError"));
          });
        }),
      ),
    );

    const { apiFetch } = await import("@/api/client");
    const promise = apiFetch("/health");
    const assertion = expect(promise).rejects.toMatchObject({ code: "api_timeout" });
    await vi.advanceTimersByTimeAsync(8000);
    await assertion;
  });

  it("throws api_network when fetch rejects", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))));

    const { apiFetch } = await import("@/api/client");
    await expect(apiFetch("/health")).rejects.toMatchObject({ code: "api_network" });
  });

  it("throws api_http_error with server detail on non-OK response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          new Response(JSON.stringify({ detail: "Connection must be tested" }), {
            status: 400,
            headers: { "Content-Type": "application/json" },
          }),
        ),
      ),
    );

    const { apiFetch } = await import("@/api/client");
    await expect(apiFetch("/connections")).rejects.toMatchObject({
      message: "Connection must be tested",
      status: 400,
      code: "api_http_error",
    });
  });
});
