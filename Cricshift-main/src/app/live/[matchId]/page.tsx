"use client";

import { use } from "react";
import { Navbar } from "@/components/cricshift/navbar";
import { useLiveMatch, useLiveMatchIntelligence, useLiveWebSocket } from "@/lib/api/live";
import { Loader2, Activity, Gauge, Target, Crown, TrendingUp, BarChart2, Radio, Sparkles, Zap, ShieldAlert } from "lucide-react";
import { LoadingState, ErrorState } from "@/components/cricshift/states";
import { MatchCard } from "@/components/cricshift/match-card";
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
  Area, AreaChart, Bar, BarChart, Cell,
  CartesianGrid, Line, LineChart,
  ReferenceDot, ReferenceLine, ReferenceArea,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

/* ── Shared styles ── */
const darkTooltip = {
  background: "rgba(11,11,11,0.95)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 10, fontSize: 11, color: "#f5f7fa",
  boxShadow: "0 8px 30px -8px rgba(0,0,0,0.8)", padding: "8px 10px",
};
const axisTick = { fill: "#525252", fontSize: 10 };

/* ── Skeleton card for charts still loading ── */
function ChartSkeleton({ height = "h-64" }: { height?: string }) {
  return (
    <div className={`flex ${height} items-center justify-center`}>
      <div className="flex flex-col items-center gap-3 text-muted-foreground">
        <Loader2 className="h-6 w-6 animate-spin text-emerald-500/60" />
        <p className="text-xs">Running ML predictions…</p>
      </div>
    </div>
  );
}

/* ── Helpers ── */
function crickOversToTotalBalls(overRaw: number) {
  const completed = Math.floor(overRaw);
  const balls = Math.round((overRaw % 1) * 10);
  return completed * 6 + balls;
}

export default function LiveMatchIntelligencePage({
  params,
}: {
  params: Promise<{ matchId: string }>;
}) {
  const { matchId } = use(params);
  // matchLoading: only blocks until the lightweight /match endpoint responds (~1-2s)
  const { data: match, isLoading: matchLoading } = useLiveMatch(matchId);
  // intelLoading: intelligence runs heavier ML; we render skeleton charts while it loads
  const { data: restIntelligence, isLoading: intelLoading } = useLiveMatchIntelligence(matchId);
  const { data: wsIntelligence, isConnected: wsConnected } = useLiveWebSocket(matchId);

  const intelligence = wsIntelligence || restIntelligence;

  // Only block full-page render until the basic match state is available
  if (matchLoading) {
    return (
      <div className="relative flex min-h-screen flex-col">
        <Navbar />
        <main className="flex flex-1 items-center justify-center pt-28">
          <LoadingState variant="inline" label="Fetching match data…" />
        </main>
      </div>
    );
  }

  if (!match) {
    return (
      <div className="relative flex min-h-screen flex-col">
        <Navbar />
        <main className="flex flex-1 items-center justify-center pt-28 px-4">
          <ErrorState
            title="Match not found"
            message="This match may have ended or is no longer available."
            onRetry={() => { window.location.href = "/live"; }}
            retryLabel="Back to Live Matches"
          />
        </main>
      </div>
    );
  }

  // Intelligence may still be loading — use empty arrays as fallback so charts
  // render their skeleton state without blocking the entire page
  const rawTimeline: Record<string, any>[] = intelligence?.timeline || [];
  const teamA: string = match.team_a || match.batting_team || "Team A";
  const teamB: string = match.team_b || match.bowling_team || "Team B";
  const turningPoints: Record<string, any>[] = intelligence?.turning_points || [];
  const aiCommentary: Record<string, any> | null = intelligence?.ai_commentary || null;

  /* ── Baseline fallback ─────────────────────────────────────────────────────
   * A genuinely live match that has only just started (or whose ball-by-ball
   * feed hasn't arrived yet) can return an empty ML timeline. Rather than show
   * "Waiting for data…" for a match that clearly has a score, we synthesise a
   * minimal two-point baseline from the /match scorecard so every chart still
   * renders a sensible starting line. This only kicks in when intelligence has
   * finished loading AND we actually have a score to anchor on.               */
  const matchScoreStr: string = (match as any).team_a_score ?? "";
  const baseScore = matchScoreStr && matchScoreStr.includes("/")
    ? parseInt(matchScoreStr.split("/")[0] || "0", 10)
    : 0;
  const baseOver = Number((match as any).overs ?? 0) || 0;

  const timeline: Record<string, any>[] =
    rawTimeline.length > 0
      ? rawTimeline
      : (!intelLoading && baseScore > 0)
        ? [
            { over: 0, score: 0, wickets: 0, momentum_probabilities: { Positive: 0.5 }, win_probability: {} },
            {
              over: baseOver || 1,
              score: baseScore,
              wickets:
                matchScoreStr.includes("/")
                  ? parseInt(matchScoreStr.split("/")[1] || "0", 10)
                  : 0,
              momentum_probabilities: { Positive: 0.5 },
              win_probability: {},
            },
          ]
        : [];

  /* ── Scoreboard numbers ──────────────────────────────────────────────────
   * Prefer live timeline data when available; fall back to the /match endpoint
   * fields that are already present the moment matchLoading resolves.        */
  const lastPoint = timeline.length > 0 ? timeline[timeline.length - 1] : null;

  // Score / wickets: timeline wins when loaded; otherwise parse from team_a_score
  const scoreStr: string = (match as any).team_a_score ?? "";
  const parsedScore = scoreStr && scoreStr !== "-"
    ? parseInt(scoreStr.split("/")[0] ?? "0", 10)
    : 0;
  const parsedWickets = scoreStr && scoreStr.includes("/")
    ? parseInt(scoreStr.split("/")[1] ?? "0", 10)
    : 0;

  const score: number   = lastPoint?.score   ?? parsedScore;
  const wickets: number = lastPoint?.wickets ?? parsedWickets;

  // Overs: prefer match endpoint's overs field which is populated immediately
  const overRaw: number = lastPoint?.over ?? (match as any).overs ?? 0;
  const totalBalls = crickOversToTotalBalls(overRaw);

  const crr = totalBalls > 0 ? (score / totalBalls) * 6 : 0;
  const target: number = (match as any).target ?? 0;
  const runsNeeded = Math.max(0, target - score);
  const ballsLeft = Math.max(0, 120 - totalBalls);
  const rrr = target > 0 && ballsLeft > 0 && runsNeeded > 0 ? (runsNeeded / ballsLeft) * 6 : null;
  // Format-aware projection. max_overs comes from the /match endpoint (derived
  // from the live feed: T20=20, ODI=50). Use the standard "current runs +
  // run-rate x balls-remaining" formula, scoped to THIS innings length. Only
  // project a limited-overs innings that isn't already complete (no Tests).
  const maxOvers = Number((match as any).max_overs) || 20;
  const maxBalls = maxOvers * 6;
  const projected =
    totalBalls > 0 && totalBalls < maxBalls && maxOvers <= 50
      ? Math.round(score + (score / totalBalls) * (maxBalls - totalBalls))
      : null;

  /* ── Chart data ── */
  const momentumData = timeline.map((t) => ({
    over: t.over,
    m: t.momentum_probabilities?.Positive != null ? t.momentum_probabilities.Positive * 100 : 50,
    wickets: t.wickets ?? 0,
  }));

  /* Detect overs where a wicket fell (change in wicket count) */
  const wicketOvers: number[] = [];
  for (let i = 1; i < timeline.length; i++) {
    if ((timeline[i].wickets ?? 0) > (timeline[i - 1].wickets ?? 0)) {
      wicketOvers.push(timeline[i].over);
    }
  }

  /* Turning point overs for ReferenceDot */
  const tpOvers = turningPoints.map((tp) => ({
    over: tp.over,
    m: (() => {
      const match = momentumData.find((d) => Math.abs(d.over - tp.over) < 0.6);
      return match?.m ?? 50;
    })(),
  }));

  const winProbData = timeline.map((t) => {
    const probs = t.win_probability || {};
    const keys = Object.keys(probs);
    let valA = probs[teamA];
    let valB = probs[teamB] ?? probs["Bowling Team"];
    if (valA === undefined && keys.length > 0) valA = probs[keys[0]];
    if (valB === undefined && keys.length > 1) valB = probs[keys[1]];
    if (valB === undefined && valA !== undefined) valB = 100 - valA;
    if (valA === undefined) { valA = 50; valB = 50; }
    return { over: t.over, teamA: valA, teamB: valB };
  });

  /* Score worm */
  const wormData = timeline.map((t) => ({ over: t.over, score: t.score ?? 0 }));

  /* Over-by-over run rate bar — group timeline points by completed over */
  const rrBarData: { over: number; runs: number }[] = (() => {
    const result: { over: number; runs: number }[] = [];
    let prevScore = 0;
    for (const t of timeline) {
      const ovNum = Math.floor(t.over as number);
      // ovNum >= 0 so we don't accidentally drop over 0 / the first partial over.
      // We also skip if this integer-over bucket is already represented.
      if (!result.some((r) => r.over === ovNum)) {
        const runsThisOver = Math.max(0, (t.score ?? 0) - prevScore);
        result.push({ over: ovNum, runs: runsThisOver });
        prevScore = t.score ?? 0;
      }
    }
    return result;
  })();

  return (
    <div className="relative flex min-h-screen flex-col">
      <Navbar />

      <main className="flex flex-1 flex-col px-4 pt-28 pb-20 sm:px-6 lg:px-8 max-w-[1400px] mx-auto w-full">

        {/* ── Scoreboard ── */}
        <div className="mb-8 grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 flex flex-col gap-4">
            <MatchCard match={{
              ...match,
              team_a: match.batting_team || match.team_a || "Team A",
              team_b: match.bowling_team || match.team_b || "Team B",
              // Use timeline data when available, otherwise the pre-populated match fields
              team_a_score: lastPoint
                ? `${lastPoint.score}/${lastPoint.wickets}`
                : ((match as any).team_a_score || "Yet to bat"),
              team_a_overs: lastPoint
                ? String(lastPoint.over)
                : ((match as any).team_a_overs ?? ""),
              // The /match endpoint now returns the bowling side's real innings
              // score (falling back to "Target: N" or "Yet to bat"). Prefer it.
              team_b_score:
                ((match as any).team_b_score && (match as any).team_b_score !== "-")
                  ? (match as any).team_b_score
                  : (target ? `Target: ${target}` : "Yet to bat"),
              team_b_overs: (match as any).team_b_overs ?? "",
              status: "Live Analytics Active",
              match_format: (match as any).match_format || "T20",
            }} index={0} />

            <div className="grid grid-cols-3 gap-4 rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-4">
              <div className="text-center">
                <p className="text-xs text-muted-foreground uppercase">Current RR</p>
                <p className="text-lg font-bold text-white">{totalBalls > 0 ? crr.toFixed(2) : "0.00"}</p>
              </div>
              <div className="text-center border-l border-r border-white/10">
                <p className="text-xs text-muted-foreground uppercase">Required RR</p>
                <p className="text-lg font-bold text-amber-400">{rrr !== null ? rrr.toFixed(2) : "—"}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-muted-foreground uppercase">Projected Score</p>
                <p className="text-lg font-bold text-white">{projected ?? "—"}</p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-6 flex flex-col justify-center">
            <h3 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-widest flex items-center gap-2">
              <Target className="h-4 w-4 text-emerald-400" />
              Current Phase
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Batter</p>
                <p className="font-semibold text-white truncate">
                  {intelligence?.latest_state?.batter
                    || (match as any).current_striker
                    || "—"}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Bowler</p>
                <p className="font-semibold text-white truncate">
                  {intelligence?.latest_state?.bowler
                    || (match as any).current_bowler
                    || "—"}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Momentum</p>
                {intelLoading ? (
                  <div className="h-5 w-20 rounded bg-white/10 animate-pulse" />
                ) : (
                  <p className="font-semibold text-emerald-400">
                    {intelligence?.latest_state?.momentum_class || "Neutral"}
                  </p>
                )}
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Leading</p>
                {intelLoading ? (
                  <div className="h-5 w-24 rounded bg-white/10 animate-pulse" />
                ) : (
                  <p className="font-semibold text-amber-400">
                    {intelligence?.latest_state?.win_probability
                      ? Object.entries(intelligence.latest_state.win_probability)
                          .sort(([, a], [, b]) => (b as number) - (a as number))[0][0]
                      : "Even"}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ── AI Broadcast Commentary & Tactical Insights ── */}
        {aiCommentary && (
          <div className="mb-6 rounded-2xl border border-emerald-500/20 bg-gradient-to-r from-emerald-950/20 via-zinc-900/60 to-black p-6 backdrop-blur-md shadow-[0_0_30px_rgba(0,200,83,0.05)]">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-amber-400" />
                <h3 className="text-sm font-bold uppercase tracking-widest text-emerald-400">
                  AI Broadcast Commentary & Tactical Synthesis
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${
                    aiCommentary.tone === "CRITICAL"
                      ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                      : aiCommentary.tone === "MOMENTUM_SHIFT"
                      ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  }`}
                >
                  {aiCommentary.tone}
                </span>
                <span className="text-xs font-mono text-muted-foreground bg-white/5 px-2 py-0.5 rounded border border-white/10">
                  Impact: {aiCommentary.impact_rating}/10
                </span>
              </div>
            </div>

            <h4 className="text-base font-bold text-white mb-2">
              {aiCommentary.headline}
            </h4>

            <p className="text-sm text-zinc-300 leading-relaxed mb-4">
              {aiCommentary.commentary}
            </p>

            <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-start gap-2.5">
              <Zap className="h-4 w-4 text-emerald-400 mt-0.5 shrink-0" />
              <div>
                <p className="text-xs font-semibold text-emerald-300">
                  Tactical Recommendation for Analyst & Captain:
                </p>
                <p className="text-xs text-emerald-100/90 mt-0.5 leading-relaxed">
                  {aiCommentary.tactical_insight}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ── Charts Row 1: Momentum + Win Probability ── */}
        <div className="grid gap-6 lg:grid-cols-2">

          {/* Momentum with phase zones, wicket lines, turning-point dots */}
          <div className="rounded-2xl border border-white/5 bg-[#121415] overflow-hidden flex flex-col">
            <div className="p-5 flex items-center justify-between border-b border-white/5">
              <div className="flex items-center gap-3">
                <Activity className="h-5 w-5 text-emerald-400" />
                <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">MOMENTUM</h3>
                <div className="flex items-center gap-1.5 ml-2">
                  <div className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                  <span className="text-[10px] font-bold text-red-500 uppercase tracking-wider">LIVE</span>
                </div>
              </div>
              <div className="bg-emerald-500/10 text-emerald-400 text-sm font-bold px-3 py-1 rounded-full border border-emerald-500/20">
                {intelLoading ? (
                  <span className="inline-block h-4 w-10 rounded bg-emerald-500/20 animate-pulse" />
                ) : momentumData.length > 0 ? (
                  `${Math.round(momentumData[momentumData.length - 1].m)}%`
                ) : "—"}
              </div>
            </div>

            <div className="px-5 pt-3 flex flex-wrap items-center gap-4 text-[10px] text-muted-foreground">
              <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-indigo-400/50 inline-block" />Powerplay</span>
              <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-red-400/50 inline-block" />Death</span>
              <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-amber-400 inline-block" />Turning point</span>
              <span className="flex items-center gap-1"><span className="h-px w-4 bg-red-500/50 inline-block" />Wicket</span>
            </div>

            <div
              className="h-64 w-full p-4 pl-1"
              role="img"
              aria-label="Momentum shift chart: positive-momentum probability over the course of the innings."
            >
              {intelLoading ? (
                <ChartSkeleton />
              ) : momentumData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={momentumData} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
                    <defs>
                      <linearGradient id="momLiveFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#00c853" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#00c853" stopOpacity={0} />
                      </linearGradient>
                    </defs>

                    {/* Phase zone overlays */}
                    <ReferenceArea x1={0} x2={6}  fill="rgba(99,102,241,0.06)" />
                    <ReferenceArea x1={16} x2={20} fill="rgba(239,68,68,0.06)" />
                    {/* 50% reference line */}
                    <ReferenceLine y={50} stroke="rgba(255,255,255,0.12)" strokeDasharray="4 3" />

                    {/* Wicket vertical lines */}
                    {wicketOvers.map((ov) => (
                      <ReferenceLine key={ov} x={ov} stroke="rgba(239,68,68,0.45)" strokeWidth={1.5} strokeDasharray="3 2" />
                    ))}

                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                    <XAxis dataKey="over" tick={axisTick} axisLine={false} tickLine={false} />
                    <YAxis domain={[0, 100]} ticks={[0, 50, 100]} tick={axisTick}
                      tickFormatter={(v) => `${v}%`} axisLine={false} tickLine={false} width={36} />
                    <Tooltip contentStyle={darkTooltip}
                      labelFormatter={(l) => `Over ${l}`}
                      formatter={(v: number) => [`${v.toFixed(1)}%`, "Positive Momentum"]} />
                    <Area type="monotone" dataKey="m" stroke="#00c853" strokeWidth={2}
                      fill="url(#momLiveFill)" connectNulls={true}
                      activeDot={{ r: 5, fill: "#fff", stroke: "#00c853", strokeWidth: 2 }} />

                    {/* Turning point dots */}
                    {tpOvers.map((tp, i) => (
                      <ReferenceDot key={i} x={tp.over} y={tp.m}
                        r={7} fill="#ffc107" stroke="#0b0b0b" strokeWidth={2}
                        label={{ value: "⚡", position: "top", fontSize: 10 }} />
                    ))}
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                  Waiting for match data…
                </div>
              )}
            </div>
          </div>

          {/* Win Probability with 50% line + Y labels */}
          <div className="rounded-2xl border border-white/5 bg-[#121415] overflow-hidden flex flex-col">
            <div className="p-5 flex items-center justify-between border-b border-white/5">
              <div className="flex items-center gap-3">
                <Gauge className="h-5 w-5 text-emerald-400" />
                <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">WIN PROBABILITY</h3>
              </div>
              <div className="bg-emerald-500/10 text-emerald-400 text-sm font-bold px-3 py-1 rounded-full border border-emerald-500/20">
                {intelLoading ? (
                  <span className="inline-block h-4 w-16 rounded bg-emerald-500/20 animate-pulse" />
                ) : winProbData.length > 0 ? (
                  winProbData[winProbData.length - 1].teamA >= 50
                    ? `${(teamA || "Team A").substring(0, 3).toUpperCase()} ${Math.round(winProbData[winProbData.length - 1].teamA)}%`
                    : `${(teamB || "Team B").substring(0, 3).toUpperCase()} ${Math.round(winProbData[winProbData.length - 1].teamB)}%`
                ) : "Even"}
              </div>
            </div>

            <div className="px-5 pt-3 flex items-center gap-6">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                <span className="text-xs text-muted-foreground">{teamA}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                <span className="text-xs text-muted-foreground">{teamB}</span>
              </div>
            </div>

            <div
              className="h-64 w-full p-4 pl-1"
              role="img"
              aria-label={`Win probability chart over the innings, comparing ${teamA} and ${teamB}.`}
            >
              {intelLoading ? (
                <ChartSkeleton />
              ) : winProbData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={winProbData} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
                    <defs>
                      <linearGradient id="teamALiveFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#00c853" stopOpacity={0.2} />
                        <stop offset="100%" stopColor="#00c853" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="teamBLiveFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#ffc107" stopOpacity={0.15} />
                        <stop offset="100%" stopColor="#ffc107" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    {/* 50% "even" line */}
                    <ReferenceLine y={50} stroke="rgba(255,255,255,0.18)" strokeDasharray="4 3"
                      label={{ value: "50%", position: "insideTopRight", fill: "#6b7280", fontSize: 9 }} />
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                    <XAxis dataKey="over" tick={axisTick} axisLine={false} tickLine={false} />
                    <YAxis domain={[0, 100]} ticks={[0, 25, 50, 75, 100]}
                      tick={axisTick} tickFormatter={(v) => `${v}%`} axisLine={false} tickLine={false} width={36} />
                    <Tooltip contentStyle={darkTooltip} labelFormatter={(l) => `Over ${l}`}
                      formatter={(v: number, n: string) => [`${v.toFixed(1)}%`, n === "teamA" ? teamA : teamB]} />
                    <Area type="monotone" dataKey="teamA" stroke="#00c853" strokeWidth={2} fill="url(#teamALiveFill)" connectNulls={true}
                      activeDot={{ r: 5, fill: "#00c853", stroke: "#fff", strokeWidth: 2 }} />
                    <Area type="monotone" dataKey="teamB" stroke="#ffc107" strokeWidth={2} fill="url(#teamBLiveFill)" connectNulls={true}
                      activeDot={{ r: 5, fill: "#ffc107", stroke: "#fff", strokeWidth: 2 }} />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                  Waiting for data…
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── Charts Row 2: Score Worm + Run Rate Bars ── */}
        <div className="mt-6 grid gap-6 lg:grid-cols-2">

          {/* Score worm */}
          <div className="rounded-2xl border border-white/5 bg-[#121415] overflow-hidden">
            <div className="p-5 border-b border-white/5 flex items-center gap-3">
              <TrendingUp className="h-5 w-5 text-indigo-400" />
              <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">SCORE WORM</h3>
            </div>
            <div className="h-52 p-4 pl-1">
              {intelLoading ? (
                <ChartSkeleton height="h-52" />
              ) : wormData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={wormData} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
                    {/* Wicket lines on worm too */}
                    {wicketOvers.map((ov) => (
                      <ReferenceLine key={ov} x={ov} stroke="rgba(239,68,68,0.4)" strokeWidth={1.5} strokeDasharray="3 2" />
                    ))}
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                    <XAxis dataKey="over" tick={axisTick} axisLine={false} tickLine={false} />
                    <YAxis tick={axisTick} axisLine={false} tickLine={false} width={36} />
                    <Tooltip contentStyle={darkTooltip} labelFormatter={(l) => `Over ${l}`}
                      formatter={(v: number) => [v, "Score"]} />
                    <Line type="monotone" dataKey="score" stroke="#818cf8" strokeWidth={2.5} dot={false} connectNulls={true}
                      activeDot={{ r: 5, fill: "#818cf8", stroke: "#fff", strokeWidth: 2 }} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                  Waiting for data…
                </div>
              )}
            </div>
          </div>

          {/* Over-by-over run rate bars */}
          <div className="rounded-2xl border border-white/5 bg-[#121415] overflow-hidden">
            <div className="p-5 border-b border-white/5 flex items-center gap-3">
              <BarChart2 className="h-5 w-5 text-amber-400" />
              <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">RUNS PER OVER</h3>
            </div>
            <div className="h-52 p-4 pl-1">
              {intelLoading ? (
                <ChartSkeleton height="h-52" />
              ) : rrBarData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={rrBarData} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                    <XAxis dataKey="over" tick={axisTick} axisLine={false} tickLine={false} />
                    <YAxis tick={axisTick} axisLine={false} tickLine={false} width={28} />
                    <Tooltip contentStyle={darkTooltip} labelFormatter={(l) => `Over ${l}`}
                      formatter={(v: number) => [v, "Runs"]} />
                    <Bar dataKey="runs" radius={[3, 3, 0, 0]} maxBarSize={24}>
                      {rrBarData.map((d, i) => (
                        <Cell
                          key={i}
                          fill={d.runs >= 10 ? "#00c853" : d.runs >= 6 ? "#ffc107" : "#6b7280"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                  Waiting for data…
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── Recommend + WhatIf ── */}
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <RecommendPlayer matchState={intelligence?.latest_state ? {
              ...intelligence.latest_state, ...match,
              batting_team: match.team_a, bowling_team: match.team_b,
              current_score: lastPoint?.score || 0,
              current_wickets: lastPoint?.wickets || 0,
              overs: lastPoint?.over || 0,
            } : null} />
          </div>
          <div className="lg:col-span-2">
            <WhatIfSimulator matchState={intelligence?.latest_state ? {
              batting_team: match.team_a || match.batting_team || "Team A",
              bowling_team: match.team_b || match.bowling_team || "Team B",
              venue: (match as any).venue || "Unknown",
              // A live target (>0) means it's the chasing 2nd innings.
              innings: target > 0 ? 2 : 1,
              target: target || 0,
              current_score: lastPoint?.score ?? score ?? 0,
              current_wickets: lastPoint?.wickets ?? wickets ?? 0,
              overs: lastPoint?.over ?? overRaw ?? 0,
              current_striker: intelligence.latest_state.batter
                || (match as any).current_striker || "Unknown",
              current_bowler: intelligence.latest_state.bowler
                || (match as any).current_bowler || "Unknown",
              season: (match as any).season,
            } : null} />
          </div>
        </div>

        {/* ── Turning Points ── */}
        <div className="mt-6 rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-6">
          <h3 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-widest flex items-center gap-2">
            <Crown className="h-4 w-4 text-emerald-400" />
            AI Explainability — Momentum Shifts & Turning Points
          </h3>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {turningPoints.length > 0 ? (
              turningPoints.map((tp, i) => {
                const probs = tp.win_prob || {};
                const keys = Object.keys(probs);
                let valA = probs[teamA];
                let valB = probs[teamB];
                if (valA === undefined && keys.length > 0) valA = probs[keys[0]];
                if (valB === undefined && keys.length > 1) valB = probs[keys[1]];
                if (valB === undefined && valA !== undefined) valB = 100 - valA;

                const nameA = keys[0] || teamA;
                const nameB = keys[1] || teamB;

                return (
                  <div key={i} className="flex flex-col gap-2 p-4 rounded-xl bg-white/[0.03] border border-white/5">
                    <div className="flex justify-between items-start">
                      <span className="bg-amber-500/20 text-amber-400 rounded-md px-2.5 py-1 text-xs font-mono font-bold">
                        Over {tp.over}
                      </span>
                    </div>
                    <p className="text-sm text-white mt-1 font-medium">{tp.description}</p>
                    <div className="mt-2 text-xs text-muted-foreground bg-black/40 rounded p-2.5 border border-white/5">
                      <div className="flex justify-between mb-1">
                        <span>{nameA}</span>
                        <span className="font-semibold text-emerald-400">{valA != null ? `${Number(valA).toFixed(1)}%` : "—"}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>{nameB}</span>
                        <span className="font-semibold text-amber-400">{valB != null ? `${Number(valB).toFixed(1)}%` : "—"}</span>
                      </div>
                    </div>
                    {/* AI Explainability Reason */}
                    {tp.reason && (
                      <div className="mt-3 p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-lg">
                        <p className="text-xs text-indigo-200">
                          <span className="font-semibold text-indigo-400">AI Analysis:</span> {tp.reason}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-center col-span-full">
                <p className="text-sm text-muted-foreground">
                  No major momentum shifts detected yet. Monitoring continuously…
                </p>
              </div>
            )}
          </div>
        </div>

      </main>
    </div>
  );
}
