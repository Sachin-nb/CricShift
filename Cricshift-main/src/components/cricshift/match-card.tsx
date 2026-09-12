"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Activity, MapPin } from "lucide-react";
import type { LiveMatch } from "@/lib/api/live";
import { cn } from "@/lib/utils";

export function MatchCard({ match, index }: { match: LiveMatch; index: number }) {
  // ── Display fallbacks so a card never renders blank fields ──
  const teamA = match.team_a?.trim() || "Team A";
  const teamB = match.team_b?.trim() || "Team B";
  const status = match.status?.trim() || "Live";
  const venue = match.venue?.trim() || "Venue TBC";
  const format = match.match_format?.trim() || "T20";
  const series = match.series?.trim();
  // Show a friendly placeholder instead of a bare dash when a side has no score.
  const scoreA = match.team_a_score?.trim() || "Yet to bat";
  const scoreB = match.team_b_score?.trim() || "Yet to bat";
  const metaLine = series ? `${format} • ${series}` : format;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
    >
      <Link href={`/live/${match.match_id}`}>
        <div className="group relative overflow-hidden rounded-2xl border border-white/10 bg-black/45 backdrop-blur-md p-6 transition-all hover:bg-black/55 hover:border-white/15 hover:shadow-[0_0_30px_rgba(0,200,83,0.15)]">
          {/* Status Badge */}
          <div className="mb-4 flex items-center justify-between gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400 shrink-0">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
              </span>
              {status}
            </span>
            <span className="truncate text-right text-xs font-medium text-muted-foreground">{metaLine}</span>
          </div>

          {/* Teams and Scores */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between gap-3">
              <span className="truncate text-lg font-bold text-white">{teamA}</span>
              <div className="shrink-0 text-right">
                <span className="text-lg font-bold text-white">{scoreA}</span>
                {match.team_a_overs && <span className="ml-2 text-xs text-muted-foreground">({match.team_a_overs} ov)</span>}
              </div>
            </div>

            <div className="flex items-center justify-between gap-3">
              <span className="truncate text-lg font-bold text-white">{teamB}</span>
              <div className="shrink-0 text-right">
                <span className="text-lg font-bold text-white">{scoreB}</span>
                {match.team_b_overs && <span className="ml-2 text-xs text-muted-foreground">({match.team_b_overs} ov)</span>}
              </div>
            </div>
          </div>

          <div className="mt-6 flex items-center justify-between gap-3 border-t border-white/10 pt-4">
            <div className="flex items-center gap-1.5 truncate text-xs text-muted-foreground">
              <MapPin className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{venue}</span>
            </div>
            <div className="flex shrink-0 items-center gap-1 text-sm font-medium text-emerald-400 opacity-0 transition-opacity group-hover:opacity-100">
              Analyze Intelligence
              <ArrowRight className="h-4 w-4" />
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
