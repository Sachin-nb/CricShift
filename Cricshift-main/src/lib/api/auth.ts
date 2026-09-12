/**
 * Auth API helpers — call the FastAPI /api/auth/* endpoints.
 *
 * Session token is persisted in localStorage under "cs_session_token".
 * The token is sent as an X-Session-Token header on every authenticated call.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

// ── storage key ──────────────────────────────────────────────────────────────
export const SESSION_KEY = "cs_session_token";
export const USER_KEY    = "cs_user";
// One-shot flag: set right after login/signup so the app plays the intro
// splash animation once before revealing the dashboard.
export const SPLASH_KEY  = "cs_show_splash";

/** Mark that the intro splash should play on the next protected-page load. */
export function markSplashPending() {
  if (typeof window !== "undefined") sessionStorage.setItem(SPLASH_KEY, "1");
}

/** Read + clear the splash flag (returns true if it was set). */
export function consumeSplashPending(): boolean {
  if (typeof window === "undefined") return false;
  const pending = sessionStorage.getItem(SPLASH_KEY) === "1";
  if (pending) sessionStorage.removeItem(SPLASH_KEY);
  return pending;
}

export interface AuthUser {
  id:    string;
  name:  string;
  email: string;
  role?: "user" | "admin";
}

/**
 * Read the token from whichever store holds it.
 * - localStorage  → "keep me logged in" was checked (persists across restarts)
 * - sessionStorage → not checked (cleared when the tab/browser closes)
 */
function token(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(SESSION_KEY) ?? sessionStorage.getItem(SESSION_KEY);
}

// Backend API key — sent on every request so calls succeed even when the
// backend has BACKEND_API_KEY enforcement turned on (mirrors lib/api/client.ts).
const BACKEND_API_KEY =
  process.env.NEXT_PUBLIC_BACKEND_API_KEY ?? "dev-insecure-key-change-in-production";

async function _post<T>(path: string, body: object, requireAuth = false): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (BACKEND_API_KEY) headers["X-API-Key"] = BACKEND_API_KEY;
  if (requireAuth) {
    const t = token();
    if (!t) throw new Error("Not authenticated");
    headers["X-Session-Token"] = t;
  }
  const res = await fetch(`${API_BASE}${path}`, {
    method:  "POST",
    headers,
    body:    JSON.stringify(body),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.detail ?? json.error ?? "Request failed");
  return json as T;
}

async function _get<T>(path: string): Promise<T> {
  const t = token();
  const headers: Record<string, string> = {};
  if (BACKEND_API_KEY) headers["X-API-Key"] = BACKEND_API_KEY;
  if (t) headers["X-Session-Token"] = t;
  const res = await fetch(`${API_BASE}${path}`, { headers });
  const json = await res.json();
  if (!res.ok) throw new Error(json.detail ?? json.error ?? "Request failed");
  return json as T;
}

// ── Auth actions ─────────────────────────────────────────────────────────────

/**
 * Signup step 1 — send an email verification code and get a pending token.
 * No account is created yet.
 */
export async function apiRegisterSendOtp(data: {
  name:     string;
  email:    string;
  password: string;
  mobile?:  string;
}): Promise<{ ok: boolean; pending_token: string; message: string }> {
  return _post("/api/auth/register/send-otp", data);
}

/**
 * Signup step 2 — verify the emailed code and create the account.
 * Returns the session token + user on success.
 */
export async function apiRegisterVerifyOtp(
  pending_token: string,
  otp: string,
): Promise<{ token: string; user: AuthUser }> {
  return _post("/api/auth/register/verify-otp", { pending_token, otp });
}

export async function apiLogin(data: {
  email:    string;
  password: string;
}): Promise<{ token: string; user: AuthUser }> {
  return _post("/api/auth/login", data);
}

/** Exchange a Google ID token (credential) for a CricShift session. */
export async function apiGoogleLogin(
  credential: string,
): Promise<{ token: string; user: AuthUser }> {
  return _post("/api/auth/google", { credential });
}

export interface AuthConfig {
  google: { enabled: boolean; client_id: string };
  apple:  { enabled: boolean };
}

/** Which social providers are configured on the server. */
export async function apiAuthConfig(): Promise<AuthConfig> {
  return _get("/api/auth/config");
}

export async function apiLogout(): Promise<void> {
  try { await _post("/api/auth/logout", {}, true); } catch { /* ignore */ }
}

export async function apiMe(): Promise<{ user: AuthUser }> {
  return _get("/api/auth/me");
}

// ── Face Lock (admin) ──────────────────────────────────────────────────────

/** Whether the current admin has a face registered. */
export async function apiFaceStatus(): Promise<{ enrolled: boolean; count: number }> {
  return _get("/api/auth/face/status");
}

/** Register a face (requires the admin's password re-entry). */
export async function apiFaceEnroll(
  password: string,
  descriptor: number[],
): Promise<{ ok: boolean; count: number; message: string }> {
  return _post("/api/auth/face/enroll", { password, descriptor }, true);
}

/** Remove all registered faces (password-gated). */
export async function apiFaceReset(
  password: string,
): Promise<{ ok: boolean; message: string }> {
  // descriptor is required by the shared request model but ignored server-side
  return _post("/api/auth/face/reset", { password, descriptor: [] }, true);
}

/** Verify a captured face against the admin's registered faces. */
export async function apiFaceVerify(
  descriptor: number[],
): Promise<{ ok: boolean; matched: boolean }> {
  return _post("/api/auth/face/verify", { descriptor }, true);
}

export async function apiSendOtp(
  email: string,
): Promise<{ ok: boolean; message: string; registered?: boolean }> {
  return _post("/api/auth/send-otp", { email });
}

export async function apiVerifyOtp(email: string, otp: string): Promise<{ ok: boolean; reset_token: string }> {
  return _post("/api/auth/verify-otp", { email, otp });
}

export async function apiResetPassword(reset_token: string, new_password: string): Promise<{ ok: boolean }> {
  return _post("/api/auth/reset-password", { reset_token, new_password });
}

// ── Session helpers ──────────────────────────────────────────────────────────

/**
 * Persist the session.
 * @param remember  when true, use localStorage so the login survives closing
 *                  the browser ("keep me logged in"). When false, use
 *                  sessionStorage so it's forgotten once the tab closes.
 */
export function saveSession(token: string, user: AuthUser, remember = true) {
  // Clear both stores first so a stale copy never lingers in the other one.
  clearSession();
  const store = remember ? localStorage : sessionStorage;
  store.setItem(SESSION_KEY, token);
  store.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(USER_KEY);
  sessionStorage.removeItem(SESSION_KEY);
  sessionStorage.removeItem(USER_KEY);
  // Clear the admin Face Lock unlock flag so the next admin must re-verify.
  sessionStorage.removeItem("cs_admin_face_unlocked");
}

export function getStoredToken(): string | null {
  return token();
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_KEY) ?? sessionStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}
