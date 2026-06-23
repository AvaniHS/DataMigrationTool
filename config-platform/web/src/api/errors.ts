export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string = "api_error",
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class ApiTimeoutError extends ApiError {
  constructor(timeoutMs: number) {
    super(
      `API request timed out after ${timeoutMs}ms. Start the config API on port 8000.`,
      0,
      "api_timeout",
    );
    this.name = "ApiTimeoutError";
  }
}

export class ApiNetworkError extends ApiError {
  constructor(message = "Unable to reach the config API. Is it running on port 8000?") {
    super(message, 0, "api_network");
    this.name = "ApiNetworkError";
  }
}

export function getApiErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "An unexpected error occurred.";
}
