import { apiFetch } from "./client";

export type HealthResponse = {
  status: string;
  service: string;
};

export function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}
