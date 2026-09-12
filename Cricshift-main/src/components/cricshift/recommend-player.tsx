"use client";

import { useEffect } from "react";
import { useRecommendPlayer } from "@/lib/api/phase3";
import { Loader2, UserPlus, Sparkles, TrendingUp } from "lucide-react";

export function RecommendPlayer({ matchState, className = "" }: { matchState: any, className?: string }) {
  const recommend = useRecommendPlayer();

  useEffect(() => {
    if (!matchState) return;
    
    recommend.mutate({
      batting_team: matchState.batting_team || "Team A",
      bowling_team: matchState.bowling_team || "Team B",
      venue: matchState.venue || "Unknown",
      current_score: matchState.current_score || 0,
      current_wickets: matchState.current_wickets || 0,
      current_over: matchState.overs || 0,
      required_run_rate: matchState.target && matchState.target > matchState.current_score && matchState.overs < 20
        ? ((matchState.target - matchState.current_score) / Math.max(0.1, 20 - matchState.overs))
        : 0,
      pressure_index: matchState.current_wickets > 5 ? 0.8 : 0.3,
      momentum_score: 50,
      current_batter: matchState.current_striker || "Unknown",
      current_bowler: matchState.current_bowler || "Unknown",
      dismissed_batters: [],
      top_n: 1
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [matchState?.current_score, matchState?.overs]);

  if (!matchState || recommend.isPending) {
    return (
      <div className={`rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-6 flex flex-col items-center justify-center min-h-[200px] ${className}`}>
        <Loader2 className="h-6 w-6 animate-spin text-emerald-500 mb-2" />
        <p className="text-sm text-muted-foreground">Analyzing optimal player...</p>
      </div>
    );
  }

  const rec = recommend.data?.recommendations?.[0];

  if (!rec) {
    return (
      <div className={`rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-6 flex flex-col items-center justify-center min-h-[200px] ${className}`}>
        <p className="text-sm text-muted-foreground">No recommendations available.</p>
      </div>
    );
  }

  return (
    <div className={`rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-6 relative overflow-hidden group ${className}`}>
      {/* Background glow */}
      <div className="absolute -inset-2 bg-gradient-to-br from-emerald-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-[24px] blur-xl -z-10" />
      
      <h3 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-widest flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-emerald-400" />
        Recommended Player
      </h3>
      
      <div className="flex items-start gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400 shrink-0">
          <UserPlus className="h-6 w-6" />
        </div>
        <div>
          <h4 className="text-xl font-bold text-white flex items-center gap-2">
            {rec.Player}
            <span className="text-xs font-mono bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full border border-amber-500/20">
              {Number(rec.Recommendation_Score).toFixed(1)}% Match
            </span>
          </h4>
          <p className="mt-3 text-sm text-muted-foreground leading-relaxed">
            {rec.Reason}
          </p>
          <div className="mt-4 flex items-center gap-2 text-xs font-medium text-emerald-400 bg-emerald-500/10 w-fit px-3 py-1.5 rounded-md border border-emerald-500/10">
            <TrendingUp className="h-3.5 w-3.5" />
            Expected Impact: +{(rec.Expected_Impact * 100).toFixed(1)}% Win Prob
          </div>
        </div>
      </div>
    </div>
  );
}
