"use client";

import { useState } from "react";
import { usePlayers, useSimulate } from "@/lib/api/phase3";
import { Loader2, GitBranch, ArrowRight, Activity, Gauge } from "lucide-react";

export function WhatIfSimulator({ matchState, className = "", isHistorical = false }: { matchState: any, className?: string, isHistorical?: boolean }) {
  const [search, setSearch] = useState("");
  const { data: playersData, isLoading: playersLoading } = usePlayers(search.length > 2 ? search : undefined);
  const simulate = useSimulate();
  
  const [selectedPlayer, setSelectedPlayer] = useState<string>("");
  const [role, setRole] = useState<"batter" | "bowler">("batter");
  const [errorMsg, setErrorMsg] = useState<string>("");

  const runSimulation = () => {
    if (!matchState || !selectedPlayer) return;

    // ── Sanitize the payload so it always satisfies the backend schema. ──
    // The backend (MatchStateRequest) requires:
    //   • current_over : int, 0–20   (we get a float like 15.4 → split into over+ball, clamp)
    //   • current_ball : int, 0–6
    //   • innings      : 1 or 2      (derive from matchState.innings, or infer from target)
    //   • target       : > 0 when innings == 2
    //   • current_wickets : 0–10

    // overs may arrive as 15.4 (over 15, 4 balls) or a plain number.
    const oversRaw = Number(matchState.overs ?? 0) || 0;
    let over = Math.floor(oversRaw);
    // fractional part → balls (15.4 → 4). Guard rounding noise.
    let ball = Math.round((oversRaw - over) * 10);
    if (ball > 6) { over += Math.floor(ball / 6); ball = ball % 6; }
    // Clamp to the schema's limits (T20 tops out at 20 overs).
    over = Math.max(0, Math.min(20, over));
    ball = Math.max(0, Math.min(6, ball));

    // Innings: explicit if provided, else infer (a target implies a chase = 2nd).
    const target = Math.max(0, Math.round(Number(matchState.target ?? 0) || 0));
    const innings: number = matchState.innings === 2 || matchState.innings === 1
      ? matchState.innings
      : (target > 0 ? 2 : 1);

    const wickets = Math.max(0, Math.min(10, Math.round(Number(matchState.current_wickets ?? 0) || 0)));
    const score = Math.max(0, Math.round(Number(matchState.current_score ?? 0) || 0));

    // A 2nd innings MUST have target > 0 (schema requirement). If we somehow
    // don't have one, fall back to a sensible value so the call never 422s.
    const safeTarget = innings === 2 && target <= 0 ? score + 1 : target;

    setErrorMsg("");
    simulate.mutate(
      {
        batting_team: matchState.batting_team || "Team A",
        bowling_team: matchState.bowling_team || "Team B",
        venue: matchState.venue || "Unknown",
        innings,
        current_over: over,
        current_ball: ball,
        current_score: score,
        current_wickets: wickets,
        target: safeTarget,
        batter_name: matchState.current_striker || "Unknown",
        bowler_name: matchState.current_bowler || "Unknown",
        season: String(matchState.season ?? "2024"),
        modifications: {
          [role === "batter" ? "replace_batter" : "replace_bowler"]: selectedPlayer,
        },
        scenario_name: `Replace ${role === "batter" ? (matchState.current_striker || "batter") : (matchState.current_bowler || "bowler")} with ${selectedPlayer}`,
      },
      {
        onError: (err: any) => {
          // Surface backend validation / server errors instead of failing silently.
          const detail =
            err?.detail ??
            err?.message ??
            "Simulation failed. Please try a different scenario.";
          setErrorMsg(typeof detail === "string" ? detail : JSON.stringify(detail));
        },
      },
    );
  };

  const simResult = simulate.data;

  return (
    <div className={`rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-6 ${className}`}>
      <h3 className="text-sm font-semibold text-muted-foreground mb-6 uppercase tracking-widest flex items-center gap-2">
        <GitBranch className="h-4 w-4 text-indigo-400" />
        What-If Simulator
      </h3>
      
      <div className="space-y-4">
        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Role to replace</label>
          <div className="flex gap-2">
            <button 
              onClick={() => setRole("batter")}
              className={`flex-1 py-2 text-sm rounded-lg border transition-colors ${role === "batter" ? "bg-indigo-500/20 border-indigo-500/50 text-indigo-300" : "bg-white/5 border-white/10 text-muted-foreground hover:bg-white/10"}`}
            >
              Batter ({matchState?.current_striker || "Unknown"})
            </button>
            <button 
              onClick={() => setRole("bowler")}
              className={`flex-1 py-2 text-sm rounded-lg border transition-colors ${role === "bowler" ? "bg-indigo-500/20 border-indigo-500/50 text-indigo-300" : "bg-white/5 border-white/10 text-muted-foreground hover:bg-white/10"}`}
            >
              Bowler ({matchState?.current_bowler || "Unknown"})
            </button>
          </div>
        </div>

        <div>
          <label className="text-xs text-muted-foreground mb-1 block">Select Replacement Player</label>
          <input
            type="text"
            placeholder="Search player name..."
            className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500/50"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {search.length > 2 && playersData?.players && (
            <div className="mt-2 max-h-32 overflow-y-auto rounded-lg border border-white/10 bg-black/60 p-1">
              {playersData.players.map((p: any) => (
                <button
                  key={p.Player_Name}
                  onClick={() => { setSelectedPlayer(p.Player_Name); setSearch(p.Player_Name); setErrorMsg(""); }}
                  className="w-full text-left px-3 py-1.5 text-sm text-white hover:bg-white/10 rounded-md truncate"
                >
                  {p.Player_Name}
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={runSimulation}
          disabled={!selectedPlayer || simulate.isPending}
          className="w-full mt-4 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 transition-colors"
        >
          {simulate.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Run Simulation"}
        </button>

        {errorMsg && !simulate.isPending && (
          <div className="mt-2 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2.5 text-xs text-red-300">
            {errorMsg}
          </div>
        )}
      </div>

      {simResult && !errorMsg && (
        <div className="mt-6 pt-6 border-t border-white/10 animate-in fade-in slide-in-from-bottom-4">
          <h4 className="text-sm font-semibold text-white mb-4">{simResult.scenario_name}</h4>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-black/40 rounded-xl p-4 border border-white/5">
              <p className="text-xs text-muted-foreground flex items-center gap-1 mb-2"><Gauge className="h-3 w-3" /> Win Probability</p>
              <div className="flex items-center gap-3">
                <span className="text-lg text-white">
                  {(() => {
                    const wp = simResult.original?.win_probability;
                    const team = matchState?.batting_team;
                    if (wp && team && wp[team] !== undefined) return `${Number(wp[team]).toFixed(1)}%`;
                    if (wp) { const v = Object.values(wp) as number[]; if (v.length > 0) return `${Number(v[0]).toFixed(1)}%`; }
                    return "50.0%";
                  })()}
                </span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
                <span className={`text-lg font-bold ${((simResult.delta?.win_probability_delta ?? simResult.delta?.win_prob ?? 0) as number) > 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {(() => {
                    const wp = simResult.modified?.win_probability;
                    const team = matchState?.batting_team;
                    if (wp && team && wp[team] !== undefined) return `${Number(wp[team]).toFixed(1)}%`;
                    if (wp) { const v = Object.values(wp) as number[]; if (v.length > 0) return `${Number(v[0]).toFixed(1)}%`; }
                    return "50.0%";
                  })()}
                </span>
              </div>
            </div>
            
            <div className="bg-black/40 rounded-xl p-4 border border-white/5">
              <p className="text-xs text-muted-foreground flex items-center gap-1 mb-2"><Activity className="h-3 w-3" /> Momentum</p>
              <div className="flex items-center gap-3">
                <span className="text-sm text-white">{simResult.original?.momentum_class ?? "—"}</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-bold text-indigo-400">
                  {simResult.modified?.momentum_class ?? "—"}
                </span>
              </div>
            </div>
          </div>
          
          <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-4">
            <p className="text-sm text-indigo-200 leading-relaxed">
              {simResult.explanation}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
