"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  type AuthUser,
  clearSession,
  getStoredToken,
  getStoredUser,
  saveSession,
  apiMe,
  apiLogout,
} from "@/lib/api/auth";

// ── Types ─────────────────────────────────────────────────────────────────────

interface AuthContextValue {
  user:    AuthUser | null;
  loading: boolean;
  /** Call after a successful login/register to set the session.
   *  `remember` controls persistence: true → survives browser restart. */
  setSession: (token: string, user: AuthUser, remember?: boolean) => void;
  logout: () => Promise<void>;
}

// ── Context ───────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue>({
  user:       null,
  loading:    true,
  setSession: () => {},
  logout:     async () => {},
});

// ── Provider ──────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user,    setUser]    = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  // On mount: restore session from storage and validate with /api/auth/me
  useEffect(() => {
    const stored = getStoredUser();
    if (stored) setUser(stored);          // show cached user immediately

    const token = getStoredToken();
    if (!token) { setLoading(false); return; }

    // Revalidate the token against the server. Whichever store already holds
    // it (local vs session) is preserved by keeping `remember` consistent.
    const remembered = typeof window !== "undefined"
      && localStorage.getItem("cs_session_token") !== null;

    apiMe()
      .then(({ user: serverUser }) => {
        setUser(serverUser);
        saveSession(token, serverUser, remembered);
      })
      .catch(() => {
        // Token expired or invalid — clear
        clearSession();
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const setSession = useCallback((token: string, u: AuthUser, remember = true) => {
    saveSession(token, u, remember);
    setUser(u);
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    clearSession();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, setSession, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useAuth() {
  return useContext(AuthContext);
}
