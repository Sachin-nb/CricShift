"use client";

import { PageShell } from "@/components/cricshift/page-shell";
import { MatchCard } from "@/components/cricshift/match-card";
import { LoadingState, ErrorState, EmptyState } from "@/components/cricshift/states";
import { useLiveMatches } from "@/lib/api/live";
import { Activity, RefreshCw, Radio } from "lucide-react";

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
    <PageShell
      eyebrow="Live Analytics"
      eyebrowIcon={Activity}
      title="Live Matches"
      subtitle="Select an ongoing match to analyze real-time momentum shifts, win probabilities, and AI player recommendations."
      actions={
        <div className="flex flex-col items-start gap-2 sm:items-end">
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
      }
    >
        {/* Loading — shimmer skeleton cards */}
        {isLoading && <LoadingState variant="cards" count={3} label="Loading live matches…" className="pb-20" />}

        {/* Error state with retry */}
        {isError && !isLoading && (
          <ErrorState
            title="Failed to connect to the Live API"
            message="Make sure the backend is running and reachable."
            onRetry={() => refetch()}
          />
        )}

        {/* Empty state */}
        {!isLoading && !isError && (!matches || matches.length === 0) && (
          <EmptyState
            icon={Radio}
            title="No live matches right now"
            description="The API is connected but no matches are currently in progress."
            action={
              <button
                onClick={() => refetch()}
                className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-white"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Check again
              </button>
            }
          />
        )}

        {/* Match grid */}
        {!isLoading && !isError && matches && matches.length > 0 && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 pb-20">
            {matches.map((match, i) => (
              <MatchCard key={match.match_id} match={match} index={i} />
            ))}
          </div>
        )}
    </PageShell>
  );
}
