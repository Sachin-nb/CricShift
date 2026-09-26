"use client";

import { type ReactNode } from "react";
import { motion } from "framer-motion";
import { type LucideIcon } from "lucide-react";
import { Navbar } from "@/components/cricshift/navbar";
import { cn } from "@/lib/utils";

/**
 * PageShell — the shared chrome for every content page (dashboard, live,
 * analytics, simulate, historical, about, …).
 *
 * Standardizes what previously drifted per-page:
 *   • Navbar + consistent top padding below the fixed header (pt-28)
 *   • One max-width container with consistent horizontal padding
 *   • A single header pattern: eyebrow pill + gradient title + subtitle,
 *     with an optional right-aligned actions slot
 *   • One entrance animation
 *
 * Keeps pages focused on their content instead of re-implementing headers.
 */

type MaxWidth = "4xl" | "6xl" | "7xl";

const MAX_W: Record<MaxWidth, string> = {
  "4xl": "max-w-4xl",
  "6xl": "max-w-6xl",
  "7xl": "max-w-7xl",
};

interface PageShellProps {
  /** Small eyebrow label shown in a pill above the title. */
  eyebrow?: string;
  /** Optional icon rendered inside the eyebrow pill. */
  eyebrowIcon?: LucideIcon;
  /** Main page title. The `titleAccent` portion is rendered in the emerald gradient. */
  title: string;
  /** Optional trailing part of the title rendered with the emerald gradient. */
  titleAccent?: string;
  /** Supporting sentence under the title. */
  subtitle?: string;
  /** Right-aligned actions (e.g. <ApiStatus />, refresh button). */
  actions?: ReactNode;
  /** Center the header (used by marketing-style pages like /about). */
  centered?: boolean;
  /** Container width. Defaults to 7xl. */
  maxWidth?: MaxWidth;
  /** Page content. */
  children: ReactNode;
  className?: string;
}

export function PageShell({
  eyebrow,
  eyebrowIcon: EyebrowIcon,
  title,
  titleAccent,
  subtitle,
  actions,
  centered = false,
  maxWidth = "7xl",
  children,
  className,
}: PageShellProps) {
  return (
    <div className="relative flex min-h-screen flex-col">
      <Navbar />
      <main
        className={cn(
          "mx-auto flex w-full flex-1 flex-col px-4 pt-28 pb-16 sm:px-6 lg:px-8",
          MAX_W[maxWidth],
          className,
        )}
      >
        <motion.header
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className={cn(
            "mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between",
            centered && "sm:flex-col sm:items-center sm:text-center",
          )}
        >
          <div className={cn(centered && "flex flex-col items-center")}>
            {eyebrow && (
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-4 py-1.5 text-xs font-medium text-emerald-400">
                {EyebrowIcon && <EyebrowIcon className="h-3.5 w-3.5" />}
                {eyebrow}
              </div>
            )}
            <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              {title}
              {titleAccent && (
                <>
                  {" "}
                  <span className="text-gradient-emerald">{titleAccent}</span>
                </>
              )}
            </h1>
            {subtitle && (
              <p
                className={cn(
                  "mt-2 text-base text-muted-foreground sm:text-lg",
                  centered ? "max-w-2xl" : "max-w-2xl",
                )}
              >
                {subtitle}
              </p>
            )}
          </div>
          {actions && <div className="shrink-0">{actions}</div>}
        </motion.header>

        {children}
      </main>
    </div>
  );
}
