/**
 * API Client — Phase 5
 * Lightweight fetch wrapper for the FastAPI cricket-analytics backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

// Warn at build/runtime if the env var is not set (development safeguard).
if (process.env.NODE_ENV !== "test" && !process.env.NEXT_PUBLIC_API_URL) {
  if (typeof window !== "undefined") {
    console.warn(
      "[cricket-analytics] NEXT_PUBLIC_API_URL is not set. " +
        "Falling back to http://127.0.0.1:8000 — this will fail in production."
    );
  }
}

// Default request timeout in milliseconds.
// Override via NEXT_PUBLIC_API_TIMEOUT_MS env var if needed.
// Live intelligence can take 8-12s for a full batch prediction run,
// so we allow a generous 30s but only 8s for simple GETs (set per-call via params).
const REQUEST_TIMEOUT_MS = Number(
  process.env.NEXT_PUBLIC_API_TIMEOUT_MS ?? "30000"
);

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? body.error ?? res.statusText;
    } catch {
      // keep statusText as fallback
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

/**
 * Returns a fetch + AbortController pair that times out after the given ms.
 */
function fetchWithTimeout(
  input: RequestInfo | URL,
  init?: RequestInit,
  timeoutMs = REQUEST_TIMEOUT_MS
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  return fetch(input, { ...init, signal: controller.signal }).finally(() =>
    clearTimeout(timer)
  );
}

const BACKEND_API_KEY =
  process.env.NEXT_PUBLIC_BACKEND_API_KEY ?? "dev-insecure-key-change-in-production";

function getDefaultHeaders(isJson = false): Record<string, string> {
  const headers: Record<string, string> = {};
  if (isJson) headers["Content-Type"] = "application/json";
  if (BACKEND_API_KEY) headers["X-API-Key"] = BACKEND_API_KEY;
  return headers;
}

export async function apiGet<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
  timeoutMs?: number
): Promise<T> {
  const url = new URL(path, API_BASE);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  const res = await fetchWithTimeout(url.toString(), {
    headers: getDefaultHeaders(false),
  }, timeoutMs);
  return handleResponse<T>(res);
}

export async function apiPost<T>(path: string, body: unknown, timeoutMs?: number): Promise<T> {
  const res = await fetchWithTimeout(`${API_BASE}${path}`, {
    method: "POST",
    headers: getDefaultHeaders(true),
    body: JSON.stringify(body),
  }, timeoutMs);
  return handleResponse<T>(res);
}

export async function apiPostForm<T>(path: string, body: FormData, timeoutMs?: number): Promise<T> {
  const res = await fetchWithTimeout(`${API_BASE}${path}`, {
    method: "POST",
    headers: getDefaultHeaders(false),
    body: body,
  }, timeoutMs);
  return handleResponse<T>(res);
}
