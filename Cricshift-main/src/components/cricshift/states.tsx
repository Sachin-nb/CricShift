"use client";

import { type ReactNode } from "react";
import { AlertCircle, RefreshCw, Inbox, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Shared data-state components — one consistent look for loading / error /
 * empty across every page. Replaces the mix of Loader2 spinners, ad-hoc
 * `animate-pulse` divs, bare error text, silent catches, and native alert()s.
 *
 *   <LoadingState variant="cards" />   // shimmer skeletons while fetching
 *   <ErrorState message="…" onRetry={refetch} />
 *   <EmptyState title="…" description="…" action={<button/>} />
 */

/* ── Skeleton primitive (uses the .skeleton shimmer utility from globals.css) ── */
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton", className)} />;
}

/* ── Loading ── */
type LoadingVariant = "cards" | "panel" | "inline";

export function LoadingState({
  variant = "panel",
  count = 3,
  label = "Loading…",
  className,
}: {
  variant?: LoadingVariant;
  count?: number;
  label?: string;
  className?: string;
}) {
  if (variant === "inline") {
    return (
      <div className={cn("flex items-center justify-center gap-3 py-10 text-sm text-muted-foreground", className)}>
        <RefreshCw className="h-4 w-4 animate-spin text-emerald-400" aria-hidden />
        <span>{label}</span>
      </div>
    );
  }

  if (variant === "cards") {
    return (
      <div
        role="status"
        aria-label={label}
        className={cn("grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3", className)}
      >
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="rounded-2xl border border-white/10 bg-black/40 p-6 backdrop-blur-md">
            <div className="mb-4 flex items-center justify-between">
              <Skeleton className="h-5 w-24 rounded-full" />
              <Skeleton className="h-4 w-20" />
            </div>
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-5 w-16" />
              </div>
              <div className="flex items-center justify-between">
                <Skeleton className="h-5 w-28" />
                <Skeleton className="h-5 w-16" />
              </div>
            </div>
            <div className="mt-6 border-t border-white/10 pt-4">
              <Skeleton className="h-4 w-28" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  // panel
  return (
    <div role="status" aria-label={label} className={cn("space-y-4", className)}>
      <Skeleton className="h-8 w-1/3" />
      <Skeleton className="h-40 w-full rounded-2xl" />
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {Array.from({ length: count }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl" />
        ))}
      </div>
    </div>
  );
}

/* ── Error ── */
export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
  retryLabel = "Try Again",
  className,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-1 items-center justify-center py-10", className)}>
      <div
        role="alert"
        className="flex max-w-md flex-col items-center gap-4 rounded-2xl border border-red-500/20 bg-red-500/5 p-10 text-center"
      >
        <AlertCircle className="h-10 w-10 text-red-400" aria-hidden />
        <div>
          <p className="font-semibold text-red-300">{title}</p>
          {message && <p className="mt-1 text-sm text-muted-foreground">{message}</p>}
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/20"
          >
            <RefreshCw className="h-4 w-4" aria-hidden />
            {retryLabel}
          </button>
        )}
      </div>
    </div>
  );
}

/* ── Empty ── */
export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
  className,
}: {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-1 items-center justify-center py-10", className)}>
      <div className="flex max-w-md flex-col items-center gap-4 rounded-2xl border border-white/10 bg-black/40 p-10 text-center backdrop-blur-md">
        <Icon className="h-10 w-10 text-muted-foreground/30" aria-hidden />
        <div>
          <p className="font-medium text-white">{title}</p>
          {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
        </div>
        {action}
      </div>
    </div>
  );
}
