"use client";

import { useState } from "react";
import { Navbar } from "@/components/cricshift/navbar";
import { ApiStatus } from "@/components/cricshift/api-status";
import { MatchStateForm } from "@/components/cricshift/match-state-form";
import { usePlayers, useSimulation, useMonteCarloSimulation } from "@/lib/api/hooks";
import type { SimulationRequest, MonteCarloRequest } from "@/lib/api/types";
import type { MatchStateFormData } from "@/lib/api/validation";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from "recharts";
import {
  Loader2,
  AlertCircle,
  ArrowRight,
  Repeat,
  LineChart,
  Sparkles,
  Search,
  TrendingUp,
  TrendingDown,
} from "lucide-react";

/* ─────────────────────────────────────────────────────────────────────────
 * What-If Simulator
 * Two focused tools, in plain language:
 *   1. Swap a Player  — replace the current batter or bowler and see how the
 *                       win probability changes.
 *   2. Project Score  — run many simulated innings to project the final score.
 * ──────────────────────────────────────────────────────────────────────── */

type Tool = "swap" | "project";
type Role = "batter" | "bowler";

/** Pull the batting-team win % out of a simulation side, tolerant of shape. */
function winPct(side: Record<string, unknown> | undefined, battingTeam: string): number {
  if (!side) return 50;
  if (typeof side.win_probability_pct === "number") return side.win_probability_pct;
  const wp = side.win_probability as Record<string, number> | undefined;
  if (wp && typeof wp === "object") {
    if (typeof wp[battingTeam] === "number") return wp[battingTeam];
    const vals = Object.values(wp);
    if (vals.length && typeof vals[0] === "number") return vals[0];
  }
  return 50;
}

export default function SimulatePage() {
  const simulation = useSimulation();
  const monteCarlo = useMonteCarloSimulation();

  const [tool, setTool] = useState<Tool>("swap");
  const [state, setState] = useState<MatchStateFormData | null>(null);

  // Player-swap controls
  const [role, setRole] = useState<Role>("batter");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState("");
  const { data: playersData } = usePlayers({ search: search.length > 2 ? search : undefined, limit: 8 });

  // Score-projection controls
  const [iterations, setIterations] = useState(1000);

  function runSwap() {
    if (!state || !selected) return;
    const modKey = role === "batter" ? "replace_batter" : "replace_bowler";
    const replacing = role === "batter" ? state.batter_name : state.bowler_name;
    const req: SimulationRequest = {
      batting_team: state.batting_team,
      bowling_team: state.bowling_team,
      venue: state.venue,
      innings: state.innings,
      current_over: state.current_over,
      current_ball: state.current_ball,
      current_score: state.current_score,
      current_wickets: state.current_wickets,
      target: state.target,
      batter_name: state.batter_name,
      bowler_name: state.bowler_name,
      season: state.season,
      modifications: { [modKey]: selected },
      scenario_name: `Replace ${replacing || role} with ${selected}`,
    };
    simulation.mutate(req);
  }

  function runProjection() {
    if (!state) return;
    const req: MonteCarloRequest = {
      current_score: state.current_score,
      current_wickets: state.current_wickets,
      current_over: state.current_over,
      current_ball: state.current_ball,
      target: state.target > 0 ? state.target : undefined,
      num_simulations: iterations,
      batter_name: state.batter_name || undefined,
      bowler_name: state.bowler_name || undefined,
    };
    monteCarlo.mutate(req);
  }

  const ready = state !== null;

  return (
    <div className="relative min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 pt-24 pb-16 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white sm:text-3xl">
              What-If <span className="text-gradient-gold">Simulator</span>
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Change one thing about the current match and see how it would play out.
            </p>
          </div>
          <ApiStatus />
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
          {/* ── Left: the match situation ── */}
          <div className="lg:col-span-2">
            <div className="glass-card rounded-2xl p-5 sm:p-6">
              <div className="mb-4">
                <h2 className="text-sm font-semibold text-white">The Situation</h2>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Set the current match state to simulate from.
                </p>
              </div>
              <MatchStateForm
                onSubmit={(data) => setState(data)}
                isLoading={false}
                submitLabel={ready ? "Update Situation ✓" : "Set Situation →"}
              />
            </div>
          </div>

          {/* ── Right: the tools ── */}
          <div className="lg:col-span-3 space-y-6">
            {/* Tool switcher */}
            <div className="flex gap-2">
              <button
                onClick={() => setTool("swap")}
                className={`flex flex-1 items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-semibold transition-all ${
                  tool === "swap"
                    ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                    : "bg-white/5 text-muted-foreground border border-white/10 hover:text-white"
                }`}
              >
                <Repeat className="h-4 w-4" />
                Swap a Player
              </button>
              <button
                onClick={() => setTool("project")}
                className={`flex flex-1 items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-semibold transition-all ${
                  tool === "project"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                    : "bg-white/5 text-muted-foreground border border-white/10 hover:text-white"
                }`}
              >
                <LineChart className="h-4 w-4" />
                Project Final Score
              </button>
            </div>

            {!ready && (
              <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4 text-center text-xs text-muted-foreground">
                Set the match situation on the left to begin.
              </div>
            )}

            {/* ── Tool: Swap a Player ── */}
            {tool === "swap" && (
              <div className="glass-card rounded-2xl p-5 sm:p-6">
                <h2 className="text-sm font-semibold text-white mb-1">Swap a Player</h2>
                <p className="text-xs text-muted-foreground mb-4">
                  Replace who&apos;s on the field right now and see the win-probability impact.
                </p>

                {/* Role toggle */}
                <div className="flex gap-2 mb-4">
                  {(["batter", "bowler"] as Role[]).map((r) => (
                    <button
                      key={r}
                      onClick={() => setRole(r)}
                      disabled={!ready}
                      className={`flex-1 rounded-lg border py-2 text-sm capitalize transition-colors disabled:opacity-40 ${
                        role === r
                          ? "bg-amber-500/20 border-amber-500/40 text-amber-300"
                          : "bg-white/5 border-white/10 text-muted-foreground hover:text-white"
                      }`}
                    >
                      {r}{" "}
                      <span className="text-[11px] opacity-70">
                        ({r === "batter" ? state?.batter_name || "—" : state?.bowler_name || "—"})
                      </span>
                    </button>
                  ))}
                </div>

                {/* Player search */}
                <label className="mb-1.5 block text-xs text-muted-foreground">
                  Replace with
                </label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Search player name…"
                    disabled={!ready}
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setSelected(""); }}
                    className="w-full rounded-lg border border-white/10 bg-black/40 py-2.5 pl-9 pr-3 text-sm text-white placeholder:text-white/30 outline-none focus:border-amber-500/50 disabled:opacity-40"
                  />
                </div>
                {search.length > 2 && !selected && playersData?.players && (
                  <div className="mt-2 max-h-40 overflow-y-auto rounded-lg border border-white/10 bg-black/60 p-1">
                    {playersData.players.length === 0 && (
                      <p className="px-3 py-2 text-xs text-muted-foreground">No players found.</p>
                    )}
                    {playersData.players.map((p) => {
                      const name = String(p.Player_Name ?? "");
                      return (
                        <button
                          key={name}
                          onClick={() => { setSelected(name); setSearch(name); }}
                          className="w-full truncate rounded-md px-3 py-1.5 text-left text-sm text-white hover:bg-white/10"
                        >
                          {name}
                        </button>
                      );
                    })}
                  </div>
                )}

                <button
                  onClick={runSwap}
                  disabled={!ready || !selected || simulation.isPending}
                  className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-amber-500 to-amber-600 py-2.5 text-sm font-semibold text-amber-950 transition-all hover:brightness-95 disabled:opacity-40"
                >
                  {simulation.isPending ? (
                    <><Loader2 className="h-4 w-4 animate-spin" /> Simulating…</>
                  ) : (
                    <><Repeat className="h-4 w-4" /> Run the Swap</>
                  )}
                </button>

                {simulation.error && (
                  <div className="mt-4 flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/5 p-3 text-xs text-red-300">
                    <AlertCircle className="h-4 w-4 shrink-0" /> {simulation.error.message}
                  </div>
                )}

                {/* Result */}
                {simulation.data && !simulation.isPending && state && (() => {
                  const before = winPct(simulation.data.original, state.batting_team);
                  const after = winPct(simulation.data.modified, state.batting_team);
                  const delta = after - before;
                  const up = delta >= 0;
                  const origMom = String(
                    (simulation.data.original as Record<string, unknown>).momentum_class ?? "Neutral",
                  );
                  const modMom = String(
                    (simulation.data.modified as Record<string, unknown>).momentum_class ?? "Neutral",
                  );
                  return (
                    <motion.div
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mt-6 border-t border-white/10 pt-5"
                    >
                      {/* Before / after win prob */}
                      <div className="grid grid-cols-2 gap-3">
                        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-center">
                          <span className="block text-[10px] uppercase text-muted-foreground">Win % Before</span>
                          <span className="text-2xl font-bold text-white">{before.toFixed(1)}%</span>
                        </div>
                        <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-center">
                          <span className="block text-[10px] uppercase font-semibold text-amber-300">Win % After</span>
                          <span className="text-2xl font-bold text-amber-400">{after.toFixed(1)}%</span>
                        </div>
                      </div>

                      {/* Delta pill */}
                      <div className="mt-3 flex items-center justify-center">
                        <span
                          className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm font-bold ${
                            up
                              ? "border-emerald-500/30 bg-emerald-500/15 text-emerald-300"
                              : "border-rose-500/30 bg-rose-500/15 text-rose-300"
                          }`}
                        >
                          {up ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                          {up ? "+" : ""}{delta.toFixed(1)}% win probability
                        </span>
                      </div>

                      {/* Momentum shift */}
                      <div className="mt-4 flex items-center justify-center gap-3 text-xs">
                        <span className="text-muted-foreground">Momentum</span>
                        <span className="rounded-full bg-white/10 px-2.5 py-0.5 font-semibold text-zinc-200">{origMom}</span>
                        <ArrowRight className="h-3.5 w-3.5 text-amber-400" />
                        <span className="rounded-full bg-amber-500/15 px-2.5 py-0.5 font-semibold text-amber-300">{modMom}</span>
                      </div>

                      {/* AI explanation */}
                      {simulation.data.explanation && (
                        <div className="mt-4 rounded-xl border border-emerald-500/20 bg-emerald-500/[0.05] p-4">
                          <div className="mb-1 flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-emerald-400">
                            <Sparkles className="h-3.5 w-3.5" /> What this means
                          </div>
                          <p className="text-sm leading-relaxed text-zinc-200">{simulation.data.explanation}</p>
                        </div>
                      )}
                    </motion.div>
                  );
                })()}
              </div>
            )}

            {/* ── Tool: Project Final Score ── */}
            {tool === "project" && (
              <div className="glass-card rounded-2xl p-5 sm:p-6">
                <h2 className="text-sm font-semibold text-white mb-1">Project Final Score</h2>
                <p className="text-xs text-muted-foreground mb-4">
                  Simulates the rest of the innings many times to project the likely final score
                  {state?.target ? " and chances of chasing the target." : "."}
                </p>

                {/* Iteration selector */}
                <label className="mb-1.5 block text-xs text-muted-foreground">Accuracy</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { n: 500, label: "Quick" },
                    { n: 1000, label: "Balanced" },
                    { n: 2000, label: "Precise" },
                  ].map(({ n, label }) => (
                    <button
                      key={n}
                      onClick={() => setIterations(n)}
                      className={`rounded-lg border py-2 text-xs font-medium transition-colors ${
                        iterations === n
                          ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                          : "bg-white/5 border-white/10 text-muted-foreground hover:text-white"
                      }`}
                    >
                      {label}
                      <span className="block text-[10px] opacity-60">{n.toLocaleString()} runs</span>
                    </button>
                  ))}
                </div>

                <button
                  onClick={runProjection}
                  disabled={!ready || monteCarlo.isPending}
                  className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-emerald-500 to-emerald-600 py-2.5 text-sm font-semibold text-emerald-950 transition-all hover:brightness-95 disabled:opacity-40"
                >
                  {monteCarlo.isPending ? (
                    <><Loader2 className="h-4 w-4 animate-spin" /> Projecting…</>
                  ) : (
                    <><LineChart className="h-4 w-4" /> Project the Score</>
                  )}
                </button>

                {monteCarlo.error && (
                  <div className="mt-4 flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/5 p-3 text-xs text-red-300">
                    <AlertCircle className="h-4 w-4 shrink-0" /> {monteCarlo.error.message}
                  </div>
                )}

                {/* Result */}
                {monteCarlo.data && !monteCarlo.isPending && (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-6 border-t border-white/10 pt-5"
                  >
                    {/* Headline numbers */}
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                      <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-center">
                        <span className="block text-[10px] uppercase font-semibold text-emerald-300">Likely Final</span>
                        <span className="text-2xl font-bold text-emerald-400">{Math.round(monteCarlo.data.median_score)}</span>
                      </div>
                      <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-center">
                        <span className="block text-[10px] uppercase text-muted-foreground">Most Likely Range</span>
                        <span className="text-xl font-bold text-white">{monteCarlo.data.most_likely_score_range}</span>
                      </div>
                      {monteCarlo.data.target != null && (
                        <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 text-center">
                          <span className="block text-[10px] uppercase font-semibold text-amber-300">Chase Success</span>
                          <span className="text-2xl font-bold text-amber-400">{monteCarlo.data.win_probability_pct.toFixed(0)}%</span>
                        </div>
                      )}
                    </div>

                    {/* Distribution chart */}
                    <div className="mt-5 rounded-xl border border-white/10 bg-white/[0.02] p-4">
                      <div className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                        How likely each score is
                      </div>
                      <div className="h-48">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={monteCarlo.data.score_distribution} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                            <XAxis dataKey="range" tick={{ fill: "#6b7280", fontSize: 9 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: "#6b7280", fontSize: 9 }} axisLine={false} tickLine={false} width={28} />
                            <Tooltip
                              contentStyle={{
                                background: "rgba(11,11,11,0.95)",
                                border: "1px solid rgba(0,200,83,0.3)",
                                borderRadius: 8,
                                fontSize: 11,
                                color: "#f5f7fa",
                              }}
                              formatter={(val: number) => [`${val} of ${monteCarlo.data!.simulations_run.toLocaleString()} sims`, "Times"]}
                            />
                            <Bar dataKey="count" radius={[3, 3, 0, 0]}>
                              {monteCarlo.data.score_distribution.map((entry, idx) => (
                                <Cell
                                  key={idx}
                                  fill={entry.range === monteCarlo.data!.most_likely_score_range ? "#00c853" : "rgba(0,200,83,0.4)"}
                                />
                              ))}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
