"use client";

import { useState } from "react";
import { PageShell } from "@/components/cricshift/page-shell";
import { Card } from "@/components/cricshift/card";
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
  Users,
  Lock,
  Unlock,
  X,
  Plus,
  Check,
} from "lucide-react";

/* ─────────────────────────────────────────────────────────────────────────
 * What-If Simulator
 *
 * Flow:
 *   1. Set the match situation (teams, venue, over, score, …).
 *   2. Build the playing XI for BOTH teams by picking from all players, then
 *      LOCK the squads.
 *   3. Choose the current batter (from the batting squad) and current bowler
 *      (from the bowling squad).
 *   4. Tools:
 *        • Swap a Player  — replace the current batter/bowler with another
 *                           member of the SAME locked squad, see win-prob impact.
 *        • Project Score  — run many simulated innings to project the final score.
 * ──────────────────────────────────────────────────────────────────────── */

type Tool = "swap" | "project";
type Role = "batter" | "bowler";

const SQUAD_SIZE = 11;

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

/* ── Reusable searchable player picker that adds into a squad list ── */
function SquadBuilder({
  title,
  teamLabel,
  squad,
  onAdd,
  onRemove,
  disabled,
  accent,
}: {
  title: string;
  teamLabel: string;
  squad: string[];
  onAdd: (name: string) => void;
  onRemove: (name: string) => void;
  disabled: boolean;
  accent: "emerald" | "sky";
}) {
  const [search, setSearch] = useState("");
  const { data } = usePlayers({ search: search.length > 2 ? search : undefined, limit: 8 });
  const results = (data?.players ?? [])
    .map((p) => String(p.Player_Name ?? ""))
    .filter(Boolean)
    .filter((n) => !squad.includes(n));

  const accentCls =
    accent === "emerald"
      ? { ring: "focus:border-emerald-500/50", chip: "bg-emerald-500/15 text-emerald-200 border-emerald-500/30", count: "text-emerald-300" }
      : { ring: "focus:border-sky-500/50", chip: "bg-sky-500/15 text-sky-200 border-sky-500/30", count: "text-sky-300" };

  const full = squad.length >= SQUAD_SIZE;

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="flex items-center gap-1.5 text-sm font-semibold text-white">
          <Users className="h-4 w-4 text-muted-foreground" />
          {title}
        </h3>
        <span className={`text-xs font-semibold ${accentCls.count}`}>
          {squad.length}/{SQUAD_SIZE}
        </span>
      </div>
      <p className="mb-3 truncate text-[11px] text-muted-foreground">{teamLabel}</p>

      {/* Search + add */}
      {!disabled && !full && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search player to add…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={`w-full rounded-lg border border-white/10 bg-black/40 py-2 pl-9 pr-3 text-sm text-white placeholder:text-white/30 outline-none ${accentCls.ring}`}
          />
        </div>
      )}
      {!disabled && !full && search.length > 2 && (
        <div className="mt-2 max-h-40 overflow-y-auto rounded-lg border border-white/10 bg-black/60 p-1">
          {results.length === 0 && (
            <p className="px-3 py-2 text-xs text-muted-foreground">No players found.</p>
          )}
          {results.map((name) => (
            <button
              key={name}
              onClick={() => {
                onAdd(name);
                setSearch("");
              }}
              className="flex w-full items-center gap-2 truncate rounded-md px-3 py-1.5 text-left text-sm text-white hover:bg-white/10"
            >
              <Plus className="h-3.5 w-3.5 text-muted-foreground" />
              {name}
            </button>
          ))}
        </div>
      )}

      {/* Squad chips */}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {squad.length === 0 && (
          <span className="text-xs text-muted-foreground">No players added yet.</span>
        )}
        {squad.map((name) => (
          <span
            key={name}
            className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium ${accentCls.chip}`}
          >
            {name}
            {!disabled && (
              <button onClick={() => onRemove(name)} className="opacity-70 hover:opacity-100">
                <X className="h-3 w-3" />
              </button>
            )}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function SimulatePage() {
  const simulation = useSimulation();
  const monteCarlo = useMonteCarloSimulation();

  const [tool, setTool] = useState<Tool>("swap");
  const [state, setState] = useState<MatchStateFormData | null>(null);

  // ── Squads ──
  const [battingSquad, setBattingSquad] = useState<string[]>([]);
  const [bowlingSquad, setBowlingSquad] = useState<string[]>([]);
  const [locked, setLocked] = useState(false);

  // ── Current on-field players (chosen from locked squads) ──
  const [currentBatter, setCurrentBatter] = useState("");
  const [currentBowler, setCurrentBowler] = useState("");

  // ── Swap controls ──
  const [role, setRole] = useState<Role>("batter");
  const [replacement, setReplacement] = useState("");

  // ── Score-projection controls ──
  const [iterations, setIterations] = useState(1000);

  const ready = state !== null;
  const canLock =
    ready && battingSquad.length >= 2 && bowlingSquad.length >= 1;
  const currentSet = locked && currentBatter && currentBowler;

  function addTo(squad: "batting" | "bowling", name: string) {
    if (squad === "batting") {
      setBattingSquad((s) => (s.includes(name) || s.length >= SQUAD_SIZE ? s : [...s, name]));
    } else {
      setBowlingSquad((s) => (s.includes(name) || s.length >= SQUAD_SIZE ? s : [...s, name]));
    }
  }
  function removeFrom(squad: "batting" | "bowling", name: string) {
    if (squad === "batting") setBattingSquad((s) => s.filter((n) => n !== name));
    else setBowlingSquad((s) => s.filter((n) => n !== name));
  }

  function unlockSquads() {
    setLocked(false);
    setCurrentBatter("");
    setCurrentBowler("");
    setReplacement("");
    simulation.reset();
  }

  /** Effective match state with the currently-selected batter/bowler merged in. */
  function stateWithCurrent(): MatchStateFormData | null {
    if (!state) return null;
    return { ...state, batter_name: currentBatter, bowler_name: currentBowler };
  }

  // Replacement options = same-team squad members excluding the one on field.
  const replacementOptions =
    role === "batter"
      ? battingSquad.filter((n) => n !== currentBatter)
      : bowlingSquad.filter((n) => n !== currentBowler);

  function runSwap() {
    const s = stateWithCurrent();
    if (!s || !replacement) return;
    const modKey = role === "batter" ? "replace_batter" : "replace_bowler";
    const replacing = role === "batter" ? currentBatter : currentBowler;
    const req: SimulationRequest = {
      batting_team: s.batting_team,
      bowling_team: s.bowling_team,
      venue: s.venue,
      innings: s.innings,
      current_over: s.current_over,
      current_ball: s.current_ball,
      current_score: s.current_score,
      current_wickets: s.current_wickets,
      target: s.target,
      batter_name: s.batter_name,
      bowler_name: s.bowler_name,
      season: s.season,
      modifications: { [modKey]: replacement },
      scenario_name: `Replace ${replacing || role} with ${replacement}`,
    };
    simulation.mutate(req);
  }

  function runProjection() {
    const s = stateWithCurrent();
    if (!s) return;
    const req: MonteCarloRequest = {
      current_score: s.current_score,
      current_wickets: s.current_wickets,
      current_over: s.current_over,
      current_ball: s.current_ball,
      target: s.target > 0 ? s.target : undefined,
      num_simulations: iterations,
      batter_name: s.batter_name || undefined,
      bowler_name: s.bowler_name || undefined,
    };
    monteCarlo.mutate(req);
  }

  return (
    <PageShell
      eyebrow="What-If Simulator"
      eyebrowIcon={Repeat}
      title="What-If"
      titleAccent="Simulator"
      subtitle="Pick both squads, set who's on the field, then swap players to see how the match would change."
      actions={<ApiStatus />}
      maxWidth="6xl"
    >
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
          {/* ── Left: the match situation ── */}
          <div className="lg:col-span-2">
            <Card>
              <div className="mb-4">
                <h2 className="text-sm font-semibold text-white">
                  Step 1 · The Situation
                </h2>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Set the current match state to simulate from.
                </p>
              </div>
              <MatchStateForm
                onSubmit={(data) => setState(data)}
                isLoading={false}
                hidePlayers
                submitLabel={ready ? "Update Situation ✓" : "Set Situation →"}
              />
            </Card>
          </div>

          {/* ── Right: squads → current players → tools ── */}
          <div className="lg:col-span-3 space-y-6">
            {!ready && (
              <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4 text-center text-xs text-muted-foreground">
                Set the match situation on the left to begin.
              </div>
            )}

            {/* ── Step 2: Build & lock squads ── */}
            {ready && (
              <div className="glass-card rounded-2xl p-5 sm:p-6">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <h2 className="text-sm font-semibold text-white">
                      Step 2 · Playing Squads
                    </h2>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      Add players to each team from all available players, then
                      lock the squads.
                    </p>
                  </div>
                  {locked && (
                    <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/15 px-2.5 py-1 text-[11px] font-semibold text-emerald-300">
                      <Lock className="h-3 w-3" /> Locked
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <SquadBuilder
                    title="Batting XI"
                    teamLabel={state!.batting_team}
                    squad={battingSquad}
                    onAdd={(n) => addTo("batting", n)}
                    onRemove={(n) => removeFrom("batting", n)}
                    disabled={locked}
                    accent="emerald"
                  />
                  <SquadBuilder
                    title="Bowling XI"
                    teamLabel={state!.bowling_team}
                    squad={bowlingSquad}
                    onAdd={(n) => addTo("bowling", n)}
                    onRemove={(n) => removeFrom("bowling", n)}
                    disabled={locked}
                    accent="sky"
                  />
                </div>

                {!locked ? (
                  <button
                    onClick={() => setLocked(true)}
                    disabled={!canLock}
                    className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-emerald-500 to-emerald-600 py-2.5 text-sm font-semibold text-emerald-950 transition-all hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    <Lock className="h-4 w-4" />
                    Lock Squads
                  </button>
                ) : (
                  <button
                    onClick={unlockSquads}
                    className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 py-2.5 text-sm font-semibold text-white/80 transition-colors hover:bg-white/10"
                  >
                    <Unlock className="h-4 w-4" />
                    Edit Squads
                  </button>
                )}
                {!canLock && !locked && (
                  <p className="mt-2 text-center text-[11px] text-muted-foreground">
                    Add at least 2 batters and 1 bowler to lock.
                  </p>
                )}
              </div>
            )}

            {/* ── Step 3: Current batter & bowler ── */}
            {locked && (
              <div className="glass-card rounded-2xl p-5 sm:p-6">
                <h2 className="text-sm font-semibold text-white">
                  Step 3 · Who&apos;s on the field
                </h2>
                <p className="mt-0.5 mb-4 text-xs text-muted-foreground">
                  Pick the current batter and bowler from the locked squads.
                </p>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <label className="mb-1.5 block text-xs text-muted-foreground">
                      Current Batter <span className="text-emerald-400">({state!.batting_team})</span>
                    </label>
                    <select
                      value={currentBatter}
                      onChange={(e) => { setCurrentBatter(e.target.value); setReplacement(""); simulation.reset(); }}
                      className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2.5 text-sm text-white outline-none focus:border-emerald-500/50"
                    >
                      <option value="">Select batter…</option>
                      {battingSquad.map((n) => (
                        <option key={n} value={n}>{n}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1.5 block text-xs text-muted-foreground">
                      Current Bowler <span className="text-sky-400">({state!.bowling_team})</span>
                    </label>
                    <select
                      value={currentBowler}
                      onChange={(e) => { setCurrentBowler(e.target.value); setReplacement(""); simulation.reset(); }}
                      className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2.5 text-sm text-white outline-none focus:border-sky-500/50"
                    >
                      <option value="">Select bowler…</option>
                      {bowlingSquad.map((n) => (
                        <option key={n} value={n}>{n}</option>
                      ))}
                    </select>
                  </div>
                </div>
                {currentSet && (
                  <div className="mt-3 flex items-center gap-1.5 text-[11px] text-emerald-300">
                    <Check className="h-3.5 w-3.5" /> Ready to simulate.
                  </div>
                )}
              </div>
            )}

            {/* ── Step 4: Tools ── */}
            {currentSet && (
              <>
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

                {/* ── Tool: Swap a Player ── */}
                {tool === "swap" && (
                  <div className="glass-card rounded-2xl p-5 sm:p-6">
                    <h2 className="text-sm font-semibold text-white mb-1">Swap a Player</h2>
                    <p className="text-xs text-muted-foreground mb-4">
                      Replace the current batter or bowler with another member of
                      their squad and see the win-probability impact.
                    </p>

                    {/* Role toggle */}
                    <div className="flex gap-2 mb-4">
                      {(["batter", "bowler"] as Role[]).map((r) => (
                        <button
                          key={r}
                          onClick={() => { setRole(r); setReplacement(""); }}
                          className={`flex-1 rounded-lg border py-2 text-sm capitalize transition-colors ${
                            role === r
                              ? "bg-amber-500/20 border-amber-500/40 text-amber-300"
                              : "bg-white/5 border-white/10 text-muted-foreground hover:text-white"
                          }`}
                        >
                          {r}{" "}
                          <span className="text-[11px] opacity-70">
                            ({r === "batter" ? currentBatter : currentBowler})
                          </span>
                        </button>
                      ))}
                    </div>

                    {/* Replacement — from the SAME locked squad only */}
                    <label className="mb-1.5 block text-xs text-muted-foreground">
                      Replace with (from {role === "batter" ? state!.batting_team : state!.bowling_team} squad)
                    </label>
                    <select
                      value={replacement}
                      onChange={(e) => setReplacement(e.target.value)}
                      className="w-full rounded-lg border border-white/10 bg-black/40 px-3 py-2.5 text-sm text-white outline-none focus:border-amber-500/50"
                    >
                      <option value="">Select replacement…</option>
                      {replacementOptions.map((n) => (
                        <option key={n} value={n}>{n}</option>
                      ))}
                    </select>
                    {replacementOptions.length === 0 && (
                      <p className="mt-2 text-[11px] text-muted-foreground">
                        Add more players to this squad (Step 2) to have replacements.
                      </p>
                    )}

                    <button
                      onClick={runSwap}
                      disabled={!replacement || simulation.isPending}
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

                          <div className="mt-4 flex items-center justify-center gap-3 text-xs">
                            <span className="text-muted-foreground">Momentum</span>
                            <span className="rounded-full bg-white/10 px-2.5 py-0.5 font-semibold text-zinc-200">{origMom}</span>
                            <ArrowRight className="h-3.5 w-3.5 text-amber-400" />
                            <span className="rounded-full bg-amber-500/15 px-2.5 py-0.5 font-semibold text-amber-300">{modMom}</span>
                          </div>

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
                      disabled={monteCarlo.isPending}
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

                    {monteCarlo.data && !monteCarlo.isPending && (
                      <motion.div
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-6 border-t border-white/10 pt-5"
                      >
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

                        <div className="mt-5 rounded-xl border border-white/10 bg-white/[0.02] p-4">
                          <div className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                            How likely each score is
                          </div>
                          <div
                            className="h-48"
                            role="img"
                            aria-label={`Projected final score distribution. Most likely final score around ${Math.round(monteCarlo.data.median_score)}, most likely range ${monteCarlo.data.most_likely_score_range}.`}
                          >
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
              </>
            )}
          </div>
        </div>
    </PageShell>
  );
}
