"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AnimatePresence } from "framer-motion";
import { Loader2, ShieldX } from "lucide-react";
import { useAuth } from "@/context/auth-context";
import { consumeSplashPending } from "@/lib/api/auth";
import { SplashScreen } from "@/components/auth/splash-screen";

/**
 * AuthGate — global route protection.
 *
 * Wraps the whole app. Behaviour:
 *   • Public routes (login / signup / reset-password) are always accessible.
 *   • Every other route requires an authenticated user. If none, the user is
 *     redirected to /login.
 *   • Admin routes (/admin*) additionally require the user's role to be "admin";
 *     non-admins are bounced to the home page.
 *   • While the session is being restored/validated we show a full-screen
 *     loader so protected content never flashes before the redirect.
 *
 * "Keep me logged in" is handled in the auth layer: a remembered session lives
 * in localStorage (survives browser restart), so on next open the user lands
 * straight in the app without seeing the login screen.
 */

// Routes that do NOT require authentication.
const PUBLIC_PREFIXES = ["/login", "/signup", "/reset-password"];

function isPublic(pathname: string): boolean {
  return PUBLIC_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(p + "/"),
  );
}

function isAdminRoute(pathname: string): boolean {
  return pathname === "/admin" || pathname.startsWith("/admin/");
}

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  const pub = isPublic(pathname);

  // Intro splash: plays once after login/signup before the app is revealed.
  const [showSplash, setShowSplash] = useState(false);

  const adminRoute = isAdminRoute(pathname);
  const isAdmin = user?.role === "admin";

  useEffect(() => {
    if (loading) return; // wait until session restore finishes

    // Not logged in and trying to view a protected page → send to login
    if (!user && !pub) {
      router.replace("/login");
      return;
    }

    // Already logged in but sitting on an auth page → send to the home page
    if (user && pub) {
      router.replace("/");
      return;
    }

    // Logged in but not an admin, trying to open the admin console → bounce home.
    if (user && adminRoute && !isAdmin) {
      router.replace("/");
    }
  }, [user, loading, pub, adminRoute, isAdmin, pathname, router]);

  // When an authenticated user first lands on a protected page after
  // logging in, check the one-shot splash flag and play the intro.
  useEffect(() => {
    if (!loading && user && !pub) {
      if (consumeSplashPending()) setShowSplash(true);
    }
  }, [loading, user, pub]);

  // Public pages render immediately (login/signup/reset need to be visible
  // even when logged out).
  if (pub) return <>{children}</>;

  // Protected pages: while validating, or while a redirect is pending, show a
  // loader instead of the app content.
  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0b0b0b]">
        <div className="flex flex-col items-center gap-4 text-muted-foreground">
          <Loader2 className="h-8 w-8 animate-spin text-[#00c853]" />
          <p className="text-sm">Loading your session…</p>
        </div>
      </div>
    );
  }

  // Admin route but the user isn't an admin — show a brief "access denied"
  // state while the redirect above takes effect (prevents any content flash).
  if (adminRoute && !isAdmin) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0b0b0b]">
        <div className="flex max-w-sm flex-col items-center gap-3 px-6 text-center">
          <ShieldX className="h-10 w-10 text-rose-400" />
          <p className="text-lg font-semibold text-white">Admin access only</p>
          <p className="text-sm text-muted-foreground">
            This area is restricted to administrators. Redirecting you back…
          </p>
        </div>
      </div>
    );
  }

  // Authenticated (and, for /admin, an admin). Render the app and overlay the
  // splash while it plays.
  return (
    <>
      {children}
      <AnimatePresence>
        {showSplash && <SplashScreen onDone={() => setShowSplash(false)} />}
      </AnimatePresence>
    </>
  );
}
