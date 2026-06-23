type LogLevel = "debug" | "info" | "warn" | "error";

type LogContext = Record<string, unknown>;

function write(level: LogLevel, event: string, context?: LogContext): void {
  if (!import.meta.env.DEV) {
    return;
  }
  const payload = { event, ...context };
  const method = level === "debug" ? "log" : level;
  console[method](`[config-api] ${event}`, payload);
}

export const apiLogger = {
  debug: (event: string, context?: LogContext) => write("debug", event, context),
  info: (event: string, context?: LogContext) => write("info", event, context),
  warn: (event: string, context?: LogContext) => write("warn", event, context),
  error: (event: string, context?: LogContext) => write("error", event, context),
};

export function logClientError(event: string, error: unknown, context?: LogContext): void {
  apiLogger.error(event, {
    ...context,
    message: error instanceof Error ? error.message : String(error),
    stack: error instanceof Error ? error.stack : undefined,
  });
}
