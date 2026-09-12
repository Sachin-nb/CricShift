"use client";

import { motion } from "framer-motion";
import { Navbar } from "@/components/cricshift/navbar";
import { MatchCard } from "@/components/cricshift/match-card";
import { useLiveMatches } from "@/lib/api/live";
import { Activity, RefreshCw, Radio } from "lucide-react";

/* ── Skeleton card shown while loading ── */
function MatchCardSkeleton({ index }: { index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.07 }}
      className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-6 animate-pulse"
    >
      <div className="mb-4 flex items-center justify-between">
        <div className="h-5 w-24 rounded-full bg-white/10" />
        <div className="h-4 w-20 rounded bg-white/10" />
      </div>
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="h-5 w-32 rounded bg-white/10" />
          <div className="h-5 w-16 rounded bg-white/10" />
        </div>
        <div className="flex items-center justify-between">
          <div className="h-5 w-28 rounded bg-white/10" />
          <div className="h-5 w-16 rounded bg-white/10" />
        </div>
      </div>
      <div className="mt-6 flex items-center justify-between border-t border-white/10 pt-4">
        <div className="h-4 w-28 rounded bg-white/10" />
      </div>
    </motion.div>
  );
}

export default function LiveMatchesPage() {
  const {
    data: matches,
    isLoading,
    isError,
    refetch,
    isFetching,
    dataUpdatedAt,
  } = useLiveMatches();

  /* Compute "last checked X seconds ago" */
  const secondsAgo = dataUpdatedAt
    ? Math.round((Date.now() - dataUpdatedAt) / 1000)
    : null;

  return (
    <div className="relative flex min-h-screen flex-col">
      <Navbar />

      <main className="flex flex-1 flex-col pt-32 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        {/* Page header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10 flex flex-col sm:flex-row sm:items-end justify-between gap-4"
        >
          <div className="flex flex-col items-start gap-4">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-4 py-1.5 text-sm font-medium text-emerald-400">
              <Activity className="h-4 w-4" />
              Live Analytics
            </div>
            <div>
              <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
                Live Matches
              </h1>
              <p className="mt-2 max-w-2xl text-lg text-muted-foreground">
                Select an ongoing match to analyze real-time momentum shifts,
                win probabilities, and AI player recommendations.
              </p>
            </div>
          </div>

          {/* Match count badge + last-checked + manual refresh */}
          <div className="flex shrink-0 flex-col items-end gap-2">
            {!isLoading && matches && matches.length > 0 && (
              <div className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400">
                <Radio className="h-3 w-3" />
                {matches.length} live {matches.length === 1 ? "match" : "matches"}
              </div>
            )}
            {secondsAgo !== null && !isLoading && (
              <p className="text-[11px] text-muted-foreground">
                Last checked {secondsAgo}s ago
              </p>
            )}
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:border-emerald-500/30 hover:text-emerald-400 disabled:opacity-40"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
              Refresh
            </button>
          </div>
        </motion.div>

        {/* Loading — skeleton cards */}
        {isLoading && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 pb-20">
            {[0, 1, 2].map((i) => (
              <MatchCardSkeleton key={i} index={i} />
            ))}
          </div>
        )}

        {/* Error state with retry */}
        {isError && !isLoading && (
          <div className="flex flex-1 items-center justify-center">
            <div className="flex flex-col items-center gap-4 rounded-2xl border border-red-500/20 bg-red-500/5 p-10 text-center">
              <p className="text-red-400 font-medium">
                Failed to connect to the Live API.
              </p>
              <p className="text-sm text-muted-foreground">
                Make sure the backend is running on port 8000.
              </p>
              <button
                onClick={() => refetch()}
                className="inline-flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/20"
              >
                <RefreshCw className="h-4 w-4" />
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !isError && (!matches || matches.length === 0) && (
          <div className="flex flex-1 items-center justify-center">
            <div className="flex flex-col items-center gap-4 rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-10 text-center">
              <Radio className="h-10 w-10 text-muted-foreground/30" />
              <div>
                <p className="font-medium text-white">No live matches right now</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  The API is connected but no matches are currently in progress.
                </p>
              </div>
              <button
                onClick={() => refetch()}
                className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-white"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Check again
              </button>
            </div>
          </div>
        )}

        {/* Match grid */}
        {!isLoading && !isError && matches && matches.length > 0 && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 pb-20">
            {matches.map((match, i) => (
              <MatchCard key={match.match_id} match={match} index={i} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
