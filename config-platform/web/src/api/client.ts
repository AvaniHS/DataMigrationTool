import { ApiError, ApiNetworkError, ApiTimeoutError } from "@/api/errors";
import { apiLogger, logClientError } from "@/api/logger";

const rawBaseUrl = import.meta.env.VITE_API_URL ?? "/api";
const rawTimeoutMs = Number(import.meta.env.VITE_API_TIMEOUT_MS ?? 8000);

export const apiBaseUrl = rawBaseUrl.replace(/\/$/, "");
export const apiTimeoutMs = Number.isFinite(rawTimeoutMs) && rawTimeoutMs > 0 ? rawTimeoutMs : 8000;

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string | { msg: string }[] };
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (Array.isArray(body.detail) && body.detail.length > 0) {
      return body.detail.map((item) => item.msg).join("; ");
    }
  } catch {
    // Fall back to status text below.
  }
  return `Request failed: ${response.status} ${response.statusText}`;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${apiBaseUrl}${path.startsWith("/") ? path : `/${path}`}`;
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), apiTimeoutMs);

  apiLogger.debug("api_request_started", { method: init?.method ?? "GET", path });

  try {
    const response = await fetch(url, {
      ...init,
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...init?.headers,
      },
    });

    if (!response.ok) {
      const message = await readErrorMessage(response);
      apiLogger.warn("api_request_failed", { path, status: response.status, message });
      throw new ApiError(message, response.status, "api_http_error");
    }

    if (response.status === 204) {
      apiLogger.debug("api_request_completed", { path, status: response.status });
      return undefined as T;
    }

    const text = await response.text();
    apiLogger.debug("api_request_completed", { path, status: response.status });
    if (!text) {
      return undefined as T;
    }

    return JSON.parse(text) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === "AbortError") {
      apiLogger.warn("api_request_timeout", { path, timeoutMs: apiTimeoutMs });
      throw new ApiTimeoutError(apiTimeoutMs);
    }
    logClientError("api_request_network_error", error, { path });
    throw new ApiNetworkError();
  } finally {
    window.clearTimeout(timeoutId);
  }
}
