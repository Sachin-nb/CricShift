"use client";

import { useEffect, useRef, useState } from "react";
import { apiAuthConfig, apiGoogleLogin, type AuthUser } from "@/lib/api/auth";

/**
 * Social sign-in buttons (Google + Apple).
 *
 * Google:
 *   Uses Google Identity Services (GIS). It loads Google's script, renders the
 *   official Google button, and on success receives a JWT "credential" (ID
 *   token). That token is POSTed to the backend (/api/auth/google) which
 *   verifies it with Google and returns a CricShift session.
 *   The button only appears when the server reports Google is configured
 *   (GOOGLE_CLIENT_ID set); otherwise a disabled "not configured" button shows.
 *
 * Apple:
 *   Real Apple Sign-In needs a paid Apple Developer account and key setup that
 *   isn't provisioned here, so the button shows a clear "coming soon" message
 *   rather than failing silently.
 */

declare global {
  interface Window {
    google?: any;
  }
}

const GIS_SRC = "https://accounts.google.com/gsi/client";

interface SocialButtonsProps {
  /** Called with the session token + user once Google verifies successfully. */
  onSuccess: (token: string, user: AuthUser) => void;
  /** Called with a human-readable error message. */
  onError: (message: string) => void;
}

export function SocialButtons({ onSuccess, onError }: SocialButtonsProps) {
  const [clientId, setClientId] = useState<string | null>(null);
  const [googleReady, setGoogleReady] = useState(false);
  const [checking, setChecking] = useState(true);
  const googleBtnRef = useRef<HTMLDivElement>(null);

  // 1. Ask the backend whether Google is configured + get the client id
  useEffect(() => {
    let cancelled = false;
    apiAuthConfig()
      .then((cfg) => {
        if (cancelled) return;
        if (cfg.google.enabled && cfg.google.client_id) {
          setClientId(cfg.google.client_id);
        }
      })
      .catch(() => {
        /* config unavailable — treat as not configured */
      })
      .finally(() => {
        if (!cancelled) setChecking(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // 2. Load the Google Identity Services script once we have a client id
  useEffect(() => {
    if (!clientId) return;

    function init() {
      if (!window.google?.accounts?.id || !googleBtnRef.current) return;
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response: { credential: string }) => {
          try {
            const { token, user } = await apiGoogleLogin(response.credential);
            onSuccess(token, user);
          } catch (err) {
            onError(
              err instanceof Error ? err.message : "Google sign-in failed. Please try again.",
            );
          }
        },
      });
      // Render the official Google button into our container
      window.google.accounts.id.renderButton(googleBtnRef.current, {
        theme: "filled_black",
        size: "large",
        text: "continue_with",
        shape: "rectangular",
        width: 200,
      });
      setGoogleReady(true);
    }

    // Script already present?
    if (window.google?.accounts?.id) {
      init();
      return;
    }
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${GIS_SRC}"]`);
    if (existing) {
      existing.addEventListener("load", init, { once: true });
      return;
    }
    const script = document.createElement("script");
    script.src = GIS_SRC;
    script.async = true;
    script.defer = true;
    script.onload = init;
    script.onerror = () => onError("Could not load Google Sign-In. Check your connection.");
    document.head.appendChild(script);
  }, [clientId, onSuccess, onError]);

  function handleAppleClick() {
    onError(
      "Apple Sign-In isn't available yet. Please use Google or your email and password.",
    );
  }

  function handleGoogleFallbackClick() {
    onError(
      "Google Sign-In isn't configured yet. Add a GOOGLE_CLIENT_ID on the server to enable it.",
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3">
      {/* Google */}
      {clientId ? (
        <div className="relative min-h-[42px]">
          {/* Google renders its own button here */}
          <div ref={googleBtnRef} className="flex justify-center [color-scheme:dark]" />
          {!googleReady && (
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center rounded-lg border border-white/10 bg-[#0d0d0d] text-xs text-white/40">
              Loading Google…
            </div>
          )}
        </div>
      ) : (
        <button
          type="button"
          onClick={handleGoogleFallbackClick}
          disabled={checking}
          className="flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-[#0d0d0d] py-2.5 text-xs font-semibold text-white/60 transition-colors hover:bg-white/5 disabled:opacity-50"
        >
          {checking ? "…" : "Google"}
        </button>
      )}

      {/* Apple — not configured */}
      <button
        type="button"
        onClick={handleAppleClick}
        className="flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-[#0d0d0d] py-2.5 text-xs font-semibold text-white/60 transition-colors hover:bg-white/5"
      >
        Apple ID
      </button>
    </div>
  );
}
