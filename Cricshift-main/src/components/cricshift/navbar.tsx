"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, Github, LogOut, User as UserIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";

const NAV_LINKS = [
  { label: "Home",       href: "/"          },
  { label: "Live",       href: "/live"       },
  { label: "Dashboard",  href: "/dashboard"  },
  { label: "Analytics",  href: "/analytics"  },
  { label: "Simulate",   href: "/simulate"   },
  { label: "Historical", href: "/historical" },
  { label: "Admin",      href: "/admin"      },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    setOpen(false);
    router.push("/login");
  };
  
  // Custom polling health check (or use react query if available in context)
  const [apiStatus, setApiStatus] = useState<"connecting" | "connected" | "error">("connecting");
  
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/health");
        if (res.ok) setApiStatus("connected");
        else setApiStatus("error");
      } catch (e) {
        setApiStatus("error");
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="fixed inset-x-0 top-0 z-50"
    >
      <div
        className={cn(
          "mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 transition-all duration-500 sm:px-6 lg:px-8",
          scrolled
            ? "my-3 rounded-2xl border border-white/10 bg-black/60 py-2.5 backdrop-blur-xl"
            : "my-0 border border-transparent py-4",
        )}
      >
        {/* Logo */}
        <Link href="/" className="group flex items-center gap-2.5">
          <span className="relative grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 text-lg shadow-[0_0_20px_rgba(0,200,83,0.5)]">
            <span className="drop-shadow">🏏</span>
          </span>
          <span className="text-lg font-bold tracking-tight text-white">
            Cric<span className="text-gradient-emerald">Shift</span>
          </span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-1 lg:flex">
          {NAV_LINKS.filter((link) => {
            // Hide Admin from non-admins and when already inside /admin.
            if (link.href === "/admin") {
              return user?.role === "admin" && !pathname.startsWith("/admin");
            }
            return true;
          }).map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "relative rounded-lg px-3.5 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "text-white"
                    : "text-muted-foreground hover:text-white",
                )}
              >
                {link.label}
                {isActive && (
                  <motion.span
                    layoutId="nav-active"
                    className="absolute inset-x-2 -bottom-0.5 h-0.5 rounded-full bg-gradient-to-r from-emerald-400 to-amber-400"
                    transition={{
                      type: "spring",
                      stiffness: 380,
                      damping: 30,
                    }}
                  />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Right actions */}
        <div className="flex items-center gap-4">
          <div className="hidden items-center gap-2 rounded-full border border-white/5 bg-white/5 px-3 py-1.5 sm:flex">
            <span className="relative flex h-2.5 w-2.5">
              {apiStatus === "connected" && (
                <>
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
                </>
              )}
              {apiStatus === "connecting" && (
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-amber-500"></span>
              )}
              {apiStatus === "error" && (
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500"></span>
              )}
            </span>
            <span className="text-xs font-medium tracking-wide text-muted-foreground">
              {apiStatus === "connected" ? "LIVE API CONNECTED" : apiStatus === "connecting" ? "CONNECTING..." : "API DISCONNECTED"}
            </span>
          </div>

          {/* Auth actions (desktop) */}
          <div className="hidden items-center gap-2 lg:flex">
            {user ? (
              <>
                <span className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-white">
                  <UserIcon className="h-3.5 w-3.5 text-[#c8f000]" />
                  {user.name?.split(" ")[0] || "Player"}
                </span>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-white/80 transition-colors hover:bg-white/10"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="rounded-lg px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-white"
                >
                  Log In
                </Link>
                <Link
                  href="/signup"
                  className="pressable rounded-lg bg-[#c8f000] px-4 py-1.5 text-sm font-bold text-black shadow-[0_0_20px_-4px_rgba(200,240,0,0.5)] transition-all hover:brightness-95 hover:shadow-[0_0_28px_-4px_rgba(200,240,0,0.7)]"
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>

          <button
            onClick={() => setOpen((v) => !v)}
            className="grid h-9 w-9 place-items-center rounded-lg border border-white/10 bg-white/5 text-white lg:hidden"
            aria-label="Toggle menu"
          >
            {open ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {open && (
          <motion.nav
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="mx-4 overflow-hidden rounded-2xl border border-white/10 bg-black/80 backdrop-blur-xl lg:hidden"
          >
            <div className="flex flex-col p-3">
              {NAV_LINKS.filter((link) => {
                if (link.href === "/admin") {
                  return user?.role === "admin" && !pathname.startsWith("/admin");
                }
                return true;
              }).map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setOpen(false)}
                  className={cn(
                    "rounded-lg px-4 py-3 text-sm font-medium transition-colors hover:bg-white/5",
                    pathname === link.href
                      ? "text-white"
                      : "text-muted-foreground hover:text-white",
                  )}
                >
                  {link.label}
                </Link>
              ))}
              
              <div className="mt-4 flex items-center gap-2 rounded-lg bg-white/5 px-4 py-3">
                 <span className="relative flex h-2.5 w-2.5">
                  {apiStatus === "connected" ? (
                    <>
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
                    </>
                  ) : apiStatus === "connecting" ? (
                    <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-amber-500"></span>
                  ) : (
                    <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500"></span>
                  )}
                </span>
                <span className="text-sm font-medium text-muted-foreground">
                  {apiStatus === "connected" ? "LIVE API CONNECTED" : apiStatus === "connecting" ? "CONNECTING..." : "API DISCONNECTED"}
                </span>
              </div>

              {/* Auth actions (mobile) */}
              <div className="mt-3 flex flex-col gap-2">
                {user ? (
                  <>
                    <span className="flex items-center gap-2 rounded-lg bg-white/5 px-4 py-3 text-sm font-medium text-white">
                      <UserIcon className="h-4 w-4 text-[#c8f000]" />
                      {user.name || "Player"}
                    </span>
                    <button
                      onClick={handleLogout}
                      className="flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-white/80 transition-colors hover:bg-white/10"
                    >
                      <LogOut className="h-4 w-4" />
                      Logout
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      href="/login"
                      onClick={() => setOpen(false)}
                      className="rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-center text-sm font-medium text-white transition-colors hover:bg-white/10"
                    >
                      Log In
                    </Link>
                    <Link
                      href="/signup"
                      onClick={() => setOpen(false)}
                      className="rounded-lg bg-[#c8f000] px-4 py-3 text-center text-sm font-bold text-black transition-all hover:brightness-95"
                    >
                      Sign Up
                    </Link>
                  </>
                )}
              </div>
            </div>
          </motion.nav>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
