"use client";

import { type ReactNode } from "react";
import Link from "next/link";

/**
 * AuthShell — the split-screen layout shared by login / signup / reset pages.
 *
 * Left  : hero image with headline + supporting copy (hidden on small screens)
 * Right : the form card (children)
 *
 * The lime accent (#c8f000) matches the CricShift auth design mockups.
 */

interface AuthShellProps {
  /** Small eyebrow label above the headline, e.g. "LIVE WORLD CUP COVERAGE" */
  eyebrow?: string;
  /** Two-line headline. Second line is rendered in lime. */
  headlineTop: string;
  headlineBottom: string;
  /** Supporting paragraph under the headline */
  subtext: string;
  /** Optional stat/feature badges rendered at the bottom-left of the hero */
  footerSlot?: ReactNode;
  /**
   * Background image URL for the hero panel. Optional — defaults to the local,
   * on-brand stadium photo so auth pages load fast and stay consistent with the
   * rest of the app (no external image dependency).
   */
  heroImage?: string;
  /** The form card content */
  children: ReactNode;
}

/** CricShift wordmark used on the auth panels. */
function Wordmark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <span
        className={`relative grid place-items-center rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 shadow-[0_0_20px_rgba(0,200,83,0.5)] ${
          compact ? "h-7 w-7 text-sm" : "h-9 w-9 text-lg"
        }`}
      >
        <span className="drop-shadow">🏏</span>
      </span>
      <span
        className={`font-black tracking-tight ${compact ? "text-base" : "text-lg"}`}
      >
        Cric<span className="text-[#c8f000]">Shift</span>
      </span>
    </div>
  );
}

export function AuthShell({
  eyebrow,
  headlineTop,
  headlineBottom,
  subtext,
  footerSlot,
  heroImage = "/stadium-bg.jpg",
  children,
}: AuthShellProps) {
  return (
    <div className="relative flex min-h-screen w-full overflow-hidden bg-[#070707] text-white">
      {/* ── Ambient branded backdrop (covers the whole shell, behind both panels) ── */}
      <div aria-hidden className="pointer-events-none absolute inset-0">
        {/* Emerald / lime radial glows for depth */}
        <div className="absolute -left-40 -top-40 h-[36rem] w-[36rem] rounded-full bg-[radial-gradient(circle,rgba(0,200,83,0.18),transparent_65%)] blur-2xl" />
        <div className="absolute -bottom-52 right-[-8rem] h-[40rem] w-[40rem] rounded-full bg-[radial-gradient(circle,rgba(200,240,0,0.12),transparent_65%)] blur-2xl" />
        {/* Faint pitch grid texture */}
        <div
          className="absolute inset-0 opacity-[0.05]"
          style={{
            backgroundImage:
              "linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />
      </div>

      {/* ── Left hero panel ── */}
      <div className="relative hidden w-1/2 flex-col justify-between lg:flex">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url(${heroImage})` }}
        />
        {/* Layered gradients: darken for legibility + fade into the form side */}
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/65 to-black/25" />
        <div className="absolute inset-0 bg-gradient-to-r from-black/40 via-transparent to-[#070707]" />
        {/* Subtle emerald brand wash over the photo */}
        <div className="absolute inset-0 bg-[radial-gradient(900px_500px_at_20%_90%,rgba(0,200,83,0.22),transparent_60%)]" />

        {/* Logo top-left */}
        <div className="relative z-10 p-8">
          <Wordmark />
        </div>

        {/* Headline block bottom-left */}
        <div className="relative z-10 max-w-lg p-10">
          {eyebrow && (
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[#c8f000]/30 bg-[#c8f000]/10 px-3 py-1 text-[11px] font-bold uppercase tracking-widest text-[#c8f000] backdrop-blur-sm">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#c8f000]" />
              {eyebrow}
            </div>
          )}
          <h1 className="text-5xl font-black uppercase leading-[0.95] tracking-tight drop-shadow-[0_2px_20px_rgba(0,0,0,0.6)]">
            {headlineTop}
            <br />
            <span className="bg-gradient-to-r from-[#c8f000] to-emerald-400 bg-clip-text text-transparent">
              {headlineBottom}
            </span>
          </h1>
          <p className="mt-5 max-w-md text-sm leading-relaxed text-white/75">
            {subtext}
          </p>
          {footerSlot && <div className="mt-8">{footerSlot}</div>}
        </div>
      </div>

      {/* ── Diagonal lime accent line between panels ── */}
      <div
        className="pointer-events-none absolute inset-y-0 left-1/2 z-20 hidden w-px -translate-x-1/2 lg:block"
        style={{
          background:
            "linear-gradient(to bottom, transparent, #c8f000 40%, #c8f000 60%, transparent)",
          transform: "translateX(-50%) rotate(8deg) scaleY(1.4)",
          opacity: 0.6,
        }}
      />

      {/* ── Right form panel ── */}
      <div className="relative z-10 flex w-full items-center justify-center px-6 py-10 lg:w-1/2 lg:px-16">
        {/* Mobile logo */}
        <div className="absolute left-6 top-6 lg:hidden">
          <Wordmark compact />
        </div>

        {/* Glowing gradient border wrapper for a premium, elevated card */}
        <div className="relative w-full max-w-md">
          <div className="absolute -inset-px rounded-[1.75rem] bg-gradient-to-b from-[#c8f000]/40 via-white/5 to-transparent opacity-70 blur-[1px]" />
          <div className="relative rounded-3xl border border-white/10 bg-[#101010]/80 p-8 shadow-[0_30px_80px_-20px_rgba(0,0,0,0.8)] backdrop-blur-xl">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}

/** A styled text input used across all auth forms. */
export function AuthInput({
  label,
  ...props
}: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="mb-4">
      <label className="mb-1.5 block text-[11px] font-bold uppercase tracking-widest text-white/50">
        {label}
      </label>
      <input
        {...props}
        className="w-full rounded-lg border border-white/10 bg-black/40 px-4 py-3 text-sm text-white placeholder:text-white/30 outline-none transition-all focus:border-[#c8f000] focus:bg-black/60 focus:ring-2 focus:ring-[#c8f000]/30"
      />
    </div>
  );
}

/** The primary lime CTA button. */
export function AuthButton({
  children,
  loading,
  ...props
}: { loading?: boolean } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      {...props}
      disabled={loading || props.disabled}
      className="w-full rounded-lg bg-[#c8f000] py-3.5 text-sm font-black uppercase tracking-widest text-black transition-all hover:brightness-95 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
    >
      {loading ? "Please wait…" : children}
    </button>
  );
}

/** Inline error / info banner. */
export function AuthMessage({ type, text }: { type: "error" | "success"; text: string }) {
  if (!text) return null;
  return (
    <div
      className={
        type === "error"
          ? "mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2.5 text-xs text-red-300"
          : "mb-4 rounded-lg border border-[#c8f000]/30 bg-[#c8f000]/10 px-3 py-2.5 text-xs text-[#c8f000]"
      }
    >
      {text}
    </div>
  );
}

export function BackToLogin() {
  return (
    <p className="mt-6 text-center text-xs text-white/50">
      ← Back to{" "}
      <Link href="/login" className="font-bold text-[#c8f000] hover:underline">
        Login
      </Link>
    </p>
  );
}
