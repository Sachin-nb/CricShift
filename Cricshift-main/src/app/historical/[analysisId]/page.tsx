"use client";

import { use, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/cricshift/navbar";
import {
  Activity, Gauge, Target, Crown, GitBranch, Trophy,
  TrendingUp, BarChart2,
} from "lucide-react";
import { LoadingState, ErrorState } from "@/components/cricshift/states";
import dynamic from "next/dynamic";

// Lazy-load the heavier interactive tools — they render lower on the page and
// aren't needed for first paint, so keep them out of the initial route bundle.
const RecommendPlayer = dynamic(
  () => import("@/components/cricshift/recommend-player").then((m) => m.RecommendPlayer),
  { ssr: false, loading: () => <LoadingState variant="inline" label="Loading recommendations…" /> },
);
const WhatIfSimulator = dynamic(
  () => import("@/components/cricshift/what-if-simulator").then((m) => m.WhatIfSimulator),
  { ssr: false, loading: () => <LoadingState variant="inline" label="Loading simulator…" /> },
);
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Cell,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

/* ----------------------------- Tooltip style ----------------------------- */
const darkTooltip = {
  background: "rgba(11,11,11,0.92)",
  border: "1px solid rgba(0,200,83,0.3)",
  borderRadius: 10,
  fontSize: 11,
  color: "#f5f7fa",
  boxShadow: "0 8px 30px -8px rgba(0,0,0,0.8)",
  padding: "8px 10px",
};
const axisTick = { fill: "#6b7280", fontSize: 10 };

type Pt = Record<string, any>;

export default function HistoricalAnalysisDashboard({
  params,
}: {
  params: Promise<{ analysisId: string }>;
}) {
  const router = useRouter();
  const { analysisId } = use(params);

  const [data, setData] = useState<Record<string, any> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  // Which innings' analytics are shown
  const [innings, setInnings] = useState<1 | 2>(1);
  // Over selected within the current innings (index into that innings' slice)
  const [selectedIdx, setSelectedIdx] = useState<number>(0);

  function loadAnalysis() {
    setIsLoading(true);
    setLoadError(null);

    // Try sessionStorage first (fast, works right after upload).
    // Fall back to fetching from the backend if storage is empty or expired.
    const stored = sessionStorage.getItem(`analysis_${analysisId}`);
    if (stored) {
      try {
        setData(JSON.parse(stored));
        setIsLoading(false);
        return;
      } catch {
        // corrupted — fall through to fetch
      }
    }

    const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
    fetch(`${API_BASE}/api/historical/analysis/${analysisId}`)
      .then((r) => {
        if (!r.ok) throw new Error(`Server returned ${r.status}`);
        return r.json();
      })
      .then((d) => {
        if (d) setData(d);
        else setLoadError("This analysis could not be found. It may have expired.");
      })
      .catch((err) => {
        setLoadError(
          err instanceof Error
            ? `Could not load the analysis: ${err.message}`
            : "Could not load the analysis.",
        );
      })
      .finally(() => setIsLoading(false));
  }

  useEffect(() => {
    loadAnalysis();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [analysisId]);

  // Reset the over selector whenever the innings changes.
  useEffect(() => setSelectedIdx(0), [innings]);

  const match_info = data?.match_info ?? {};
  const timeline: Pt[] = data?.timeline ?? [];
  const turning_points: Pt[] = data?.turning_points ?? [];

  const teamA: string = match_info.team_a || match_info.batting_team || "Team A";
  const teamB: string = match_info.team_b || match_info.bowling_team || "Team B";

  // Which innings actually exist in the timeline (some datasets have only one).
  const availableInnings = useMemo(() => {
    const set = new Set<number>();
    timeline.forEach((t) => set.add(Number(t.innings ?? 1)));
    return Array.from(set).sort((a, b) => a - b);
  }, [timeline]);

  // The batting team for the currently-selected innings.
  const battingTeam = innings === 2 ? teamB : teamA;
  const bowlingTeam = innings === 2 ? teamA : teamB;

  // Timeline + turning points for the selected innings only.
  const inningsTimeline = useMemo(
    () => timeline.filter((t) => Number(t.innings ?? 1) === innings),
    [timeline, innings],
  );
  const inningsTurningPoints = useMemo(
    () => turning_points.filter((tp) => Number(tp.innings ?? 1) === innings),
    [turning_points, innings],
  );

  /* ── Per-innings chart datasets ─────────────────────────────────────────── */

  // Momentum: positive-momentum probability (%) over overs.
  const momentumData = useMemo(
    () =>
      inningsTimeline.map((t) => ({
        over: t.over,
        m: t.momentum_probabilities?.Positive != null
          ? t.momentum_probabilities.Positive * 100
          : 50,
      })),
    [inningsTimeline],
  );

  // Win probability: both teams over overs.
  const winProbData = useMemo(
    () =>
      inningsTimeline.map((t) => ({
        over: t.over,
        teamA: t.win_probability?.[teamA] ?? 50,
        teamB: t.win_probability?.[teamB] ?? 50,
      })),
    [inningsTimeline, teamA, teamB],
  );

  // Score worm: cumulative score across the innings.
  const wormData = useMemo(
    () => inningsTimeline.map((t) => ({ over: t.over, score: t.score ?? 0 })),
    [inningsTimeline],
  );

  // Runs per over: diff of cumulative score between consecutive over-buckets.
  const rrBarData = useMemo(() => {
    const result: { over: number; runs: number }[] = [];
    let prevScore = 0;
    for (const t of inningsTimeline) {
      const ovNum = Math.floor(Number(t.over) || 0);
      if (!result.some((r) => r.over === ovNum)) {
        const runsThisOver = Math.max(0, (t.score ?? 0) - prevScore);
        result.push({ over: ovNum, runs: runsThisOver });
        prevScore = t.score ?? 0;
      }
    }
    return result;
  }, [inningsTimeline]);

  /* ── Simulator / recommender state, scoped to the selected innings ──────── */
  const selectedState =
    inningsTimeline[Math.min(selectedIdx, inningsTimeline.length - 1)] ??
    inningsTimeline[0];

  const currentMatchState = {
    innings, // 1 or 2 — lets the simulator send the correct innings
    batting_team: battingTeam,
    bowling_team: bowlingTeam,
    venue: match_info.venue,
    current_score: selectedState?.score ?? 0,
    current_wickets: selectedState?.wickets ?? 0,
    overs: selectedState?.over ?? 0,
    // Only the chasing innings has a target.
    target: innings === 2 ? (match_info.target ?? 0) : 0,
    current_striker: selectedState?.batter ?? "Unknown",
    current_bowler: selectedState?.bowler ?? "Unknown",
    season: match_info.season,
  };

  if (isLoading) {
    return (
      <div className="relative flex min-h-screen flex-col">
        <Navbar />
        <main className="flex flex-1 items-center justify-center pt-28">
          <LoadingState variant="inline" label="Loading historical analysis…" />
        </main>
      </div>
    );
  }

  if (loadError || !data) {
    return (
      <div className="relative flex min-h-screen flex-col">
        <Navbar />
        <main className="flex flex-1 items-center justify-center pt-28 px-4">
          <ErrorState
            title="Analysis unavailable"
            message={loadError ?? "Analysis data not found or expired."}
            onRetry={() => router.push("/historical")}
            retryLabel="Upload a new dataset"
          />
        </main>
      </div>
    );
  }

  return (
    <div className="relative flex min-h-screen flex-col">
      <Navbar />

      <main className="flex flex-1 flex-col px-4 pt-28 pb-20 sm:px-6 lg:px-8 max-w-[1400px] mx-auto w-full">
        {/* Match Result Banner */}
        {match_info.result_description && (
          <div className="mb-6 rounded-2xl border border-amber-500/30 bg-gradient-to-r from-amber-950/30 via-zinc-900/60 to-black p-5 flex flex-wrap items-center justify-between gap-4 shadow-[0_0_30px_rgba(255,193,7,0.08)]">
            <div className="flex items-center gap-3">
              <div className="h-11 w-11 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center shrink-0">
                <Trophy className="h-6 w-6 text-amber-400" />
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase tracking-widest text-amber-400">Match Outcome</span>
                <h2 className="text-xl font-bold text-white mt-0.5">{match_info.result_description}</h2>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs">
              <div className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-center">
                <span className="text-muted-foreground block text-[10px] uppercase font-semibold">{teamA}</span>
                <span className="font-bold text-white text-sm">{match_info.team_a_score || "—"}</span>
              </div>
              <div className="text-muted-foreground font-bold">vs</div>
              <div className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-center">
                <span className="text-muted-foreground block text-[10px] uppercase font-semibold">{teamB}</span>
                <span className="font-bold text-amber-400 text-sm">{match_info.team_b_score || "—"}</span>
              </div>
              {match_info.target > 0 && (
                <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl px-3.5 py-2 text-center">
                  <span className="text-amber-400/80 block text-[10px] uppercase font-semibold">Target</span>
                  <span className="font-bold text-amber-300 text-sm">{match_info.target}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Header */}
        <div className="mb-6 flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-white/10 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-400 mb-3">
              Historical Replay Analysis
            </div>
            <h1 className="text-3xl font-bold text-white mb-1.5">
              {teamA} vs {teamB}
            </h1>
            <p className="text-muted-foreground text-sm">{match_info.venue} · Season {match_info.season || "IPL"}</p>
          </div>

          <div className="flex gap-3">
            <div className="rounded-xl bg-white/5 border border-white/10 px-4 py-2.5 text-center">
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-0.5">Overs (Inns {innings})</p>
              <p className="text-lg font-bold text-white">{inningsTimeline.length}</p>
            </div>
            <div className="rounded-xl bg-white/5 border border-white/10 px-4 py-2.5 text-center">
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-0.5">Turning Points</p>
              <p className="text-lg font-bold text-amber-400">{inningsTurningPoints.length}</p>
            </div>
          </div>
        </div>

        {/* ── Innings Tabs ── */}
        <div className="mb-6 flex items-center gap-2">
          {[1, 2].map((n) => {
            const exists = availableInnings.includes(n);
            const active = innings === n;
            const label = n === 1 ? teamA : teamB;
            return (
              <button
                key={n}
                onClick={() => exists && setInnings(n as 1 | 2)}
                disabled={!exists}
                className={
                  "flex-1 sm:flex-none rounded-xl border px-5 py-3 text-left transition-all " +
                  (active
                    ? "border-emerald-500/50 bg-emerald-500/15"
                    : exists
                      ? "border-white/10 bg-white/5 hover:bg-white/10"
                      : "border-white/5 bg-white/[0.02] opacity-40 cursor-not-allowed")
                }
              >
                <span className={"block text-[10px] font-bold uppercase tracking-widest " + (active ? "text-emerald-400" : "text-muted-foreground")}>
                  {n === 1 ? "1st Innings" : "2nd Innings"}
                </span>
                <span className="block text-sm font-bold text-white truncate max-w-[220px]">
                  {label}
                  {n === 2 && match_info.target > 0 && (
                    <span className="ml-1.5 text-xs font-normal text-amber-400">chasing {match_info.target}</span>
                  )}
                </span>
              </button>
            );
          })}
        </div>

        {inningsTimeline.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-10 text-center text-muted-foreground">
            No data available for this innings in the uploaded dataset.
          </div>
        ) : (
          <>
            {/* ── Charts Row 1: Momentum + Win Probability ── */}
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Momentum */}
              <div className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-6">
                <h3 className="text-sm font-semibold text-muted-foreground mb-6 uppercase tracking-widest flex items-center gap-2">
                  <Activity className="h-4 w-4 text-emerald-400" />
                  Momentum Shift — {battingTeam}
                </h3>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={momentumData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                      <defs>
                        <linearGradient id="momFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#00c853" stopOpacity={0.45} />
                          <stop offset="100%" stopColor="#00c853" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                      <XAxis dataKey="over" tick={axisTick} axisLine={false} tickLine={false} />
                      <YAxis domain={[0, 100]} tick={axisTick} axisLine={false} tickLine={false} width={32} tickFormatter={(v) => `${v}%`} />
                      <Tooltip
                        contentStyle={darkTooltip}
                        labelStyle={{ color: "#9aa6b8" }}
                        labelFormatter={(l) => `Over ${l}`}
                        formatter={(v: number) => [`${v.toFixed(1)}%`, "Positive Momentum"]}
                      />
                      <Area type="monotone" dataKey="m" stroke="#00c853" strokeWidth={2} fill="url(#momFill)" connectNulls={true} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Win Probability */}
              <div className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-6">
                <h3 className="text-sm font-semibold text-muted-foreground mb-6 uppercase tracking-widest flex items-center gap-2">
                  <Gauge className="h-4 w-4 text-amber-400" />
                  Win Probability Progression
                </h3>
                <div className="px-1 pb-3 flex items-center gap-6">
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                    <span className="text-xs text-muted-foreground">{teamA}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                    <span className="text-xs text-muted-foreground">{teamB}</span>
                  </div>
                </div>
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={winProbData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                      <defs>
                        <linearGradient id="teamAFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#00c853" stopOpacity={0.4} />
                          <stop offset="100%" stopColor="#00c853" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="teamBFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#ffc107" stopOpacity={0.3} />
                          <stop offset="100%" stopColor="#ffc107" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                      <XAxis dataKey="over" tick={axisTick} axisLine={false} tickLine={false} />
                      <YAxis domain={[0, 100]} tick={axisTick} axisLine={false} tickLine={false} width={32} tickFormatter={(v) => `${v}%`} />
                      <Tooltip
                        contentStyle={darkTooltip}
                        labelStyle={{ color: "#9aa6b8" }}
                        labelFormatter={(l) => `Over ${l}`}
                        formatter={(v: number, n: string) => [`${v.toFixed(1)}%`, n === "teamA" ? teamA : teamB]}
                      />
                      <Area type="monotone" dataKey="teamA" stroke="#00c853" strokeWidth={2} fill="url(#teamAFill)" connectNulls={true} />
                      <Area type="monotone" dataKey="teamB" stroke="#ffc107" strokeWidth={2} fill="url(#teamBFill)" connectNulls={true} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* ── Charts Row 2: Score Worm + Runs Per Over ── */}
            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              {/* Score Worm */}
              <div className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-6">
                <h3 className="text-sm font-semibold text-muted-foreground mb-6 uppercase tracking-widest flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-indigo-400" />
                  Score Worm — {battingTeam}
                </h3>
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={wormData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                      <XAxis dataKey="over" tick={axisTick} axisLine={false} tickLine={false} />
                      <YAxis tick={axisTick} axisLine={false} tickLine={false} width={32} />
                      <Tooltip contentStyle={darkTooltip} labelStyle={{ color: "#9aa6b8" }}
                        labelFormatter={(l) => `Over ${l}`} formatter={(v: number) => [v, "Score"]} />
                      <Line type="monotone" dataKey="score" stroke="#818cf8" strokeWidth={2.5} dot={false} connectNulls={true}
                        activeDot={{ r: 5, fill: "#818cf8", stroke: "#fff", strokeWidth: 2 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Runs Per Over */}
              <div className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-6">
                <h3 className="text-sm font-semibold text-muted-foreground mb-6 uppercase tracking-widest flex items-center gap-2">
                  <BarChart2 className="h-4 w-4 text-amber-400" />
                  Runs Per Over — {battingTeam}
                </h3>
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={rrBarData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                      <XAxis dataKey="over" tick={axisTick} axisLine={false} tickLine={false} />
                      <YAxis tick={axisTick} axisLine={false} tickLine={false} width={28} />
                      <Tooltip contentStyle={darkTooltip} labelStyle={{ color: "#9aa6b8" }}
                        labelFormatter={(l) => `Over ${l}`} formatter={(v: number) => [v, "Runs"]} />
                      <Bar dataKey="runs" radius={[3, 3, 0, 0]} maxBarSize={26}>
                        {rrBarData.map((d, i) => (
                          <Cell key={i} fill={d.runs >= 10 ? "#00c853" : d.runs >= 6 ? "#ffc107" : "#6b7280"} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* ── Simulator & Recommender Row ── */}
            <div className="mt-6 grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-1 flex flex-col gap-6">
                <RecommendPlayer matchState={currentMatchState} />
              </div>

              <div className="lg:col-span-2">
                <div className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-6 mb-6">
                  <h3 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-widest flex items-center gap-2">
                    <GitBranch className="h-4 w-4 text-indigo-400" />
                    Select Match Point for Simulation (Innings {innings})
                  </h3>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-muted-foreground">Start</span>
                    <input
                      type="range"
                      min={0}
                      max={Math.max(0, inningsTimeline.length - 1)}
                      value={Math.min(selectedIdx, inningsTimeline.length - 1)}
                      onChange={(e) => setSelectedIdx(Number(e.target.value))}
                      className="flex-1 accent-indigo-500"
                    />
                    <span className="text-sm font-bold text-white whitespace-nowrap">
                      Over {selectedState?.over} · {selectedState?.score ?? 0}/{selectedState?.wickets ?? 0}
                    </span>
                  </div>
                </div>

                <WhatIfSimulator matchState={currentMatchState} isHistorical={true} />
              </div>
            </div>

            {/* ── Turning Points (current innings) ── */}
            <div className="mt-6 rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-6">
              <h3 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-widest flex items-center gap-2">
                <Crown className="h-4 w-4 text-emerald-400" />
                Turning Points — Innings {innings}
              </h3>

              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {inningsTurningPoints.length > 0 ? (
                  inningsTurningPoints.map((tp: Pt, i: number) => (
                    <div key={i} className="flex flex-col gap-2 p-4 rounded-xl bg-white/[0.03] border border-white/5">
                      <div className="flex justify-between items-start">
                        <span className="bg-amber-500/20 text-amber-400 rounded-md px-2 py-1 text-xs font-mono font-bold">
                          Over {tp.over}
                        </span>
                      </div>
                      <p className="text-sm text-white mt-1 font-medium">{tp.description}</p>
                      <div className="mt-2 text-xs text-muted-foreground bg-black/40 rounded p-2 border border-white/5">
                        <div className="flex justify-between mb-1">
                          <span>{teamA}</span>
                          <span className="font-semibold text-emerald-400">{tp.win_prob?.[teamA]?.toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>{teamB}</span>
                          <span className="font-semibold text-amber-400">{tp.win_prob?.[teamB]?.toFixed(1)}%</span>
                        </div>
                      </div>
                      <div className="mt-3 p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-lg">
                        <p className="text-xs text-indigo-200">
                          <span className="font-semibold text-indigo-400">AI Analysis:</span>{" "}
                          {tp.reason || "High pressure index combined with falling wickets triggered a major momentum swing."}
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground col-span-full">
                    No major turning points detected in this innings.
                  </p>
                )}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
