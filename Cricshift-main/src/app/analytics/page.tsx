"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Navbar } from "@/components/cricshift/navbar";
import { ApiStatus } from "@/components/cricshift/api-status";
import { usePlayers, useTeams, useVenues, useMatchup, usePlayerMatchups } from "@/lib/api/hooks";
import { Input } from "@/components/ui/input";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import {
  Search,
  Users,
  Shield,
  MapPin,
  Loader2,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  Zap,
  Target,
  Swords,
  Flame,
  Crosshair,
} from "lucide-react";

type Tab = "players" | "teams" | "venues" | "matchups";

/* ─── Smart number formatter ─────────────────────────────────────── */
function fmt(val: unknown): string {
  if (val === null || val === undefined) return "—";
  if (typeof val === "boolean") return val ? "Yes" : "No";
  if (typeof val !== "number") return String(val);
  if (Number.isInteger(val)) return val.toLocaleString();
  if (val >= 100) return val.toFixed(1);
  if (val >= 10) return val.toFixed(1);
  return val.toFixed(2);
}

/* ─── Tooltip shared style ───────────────────────────────────────── */
const darkTooltip = {
  background: "rgba(11,11,11,0.95)",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 10,
  fontSize: 12,
  color: "#f5f7fa",
  boxShadow: "0 8px 30px -8px rgba(0,0,0,0.8)",
  padding: "8px 12px",
};

/* ─── Player card component ──────────────────────────────────────── */
function PlayerCard({
  player,
  index,
  expanded,
  onToggle,
}: {
  player: Record<string, unknown>;
  index: number;
  expanded: boolean;
  onToggle: () => void;
}) {
  const name = String(player["Player_Name"] ?? "Unknown");
  const matches = Number(player["Matches_Played"] ?? 0);
  const avg = Number(player["Average"] ?? 0);
  const sr = Number(player["Strike_Rate"] ?? 0);
  const impact = Number(player["Batting_Impact_Score"] ?? 0);
  const wickets = Number(player["Wickets"] ?? 0);
  const economy = Number(player["Economy"] ?? 0);
  const position = Number(player["Batting_Position"] ?? 11);

  /* Impact colour */
  const impactColor =
    impact >= 200 ? "text-emerald-400" : impact >= 80 ? "text-amber-400" : "text-muted-foreground";
  const impactBg =
    impact >= 200 ? "bg-emerald-500/15 border-emerald-500/20" : impact >= 80 ? "bg-amber-500/15 border-amber-500/20" : "bg-white/5 border-white/10";

  /* All extra columns for the expanded view */
  const extraCols = Object.entries(player).filter(
    ([k]) =>
      !["Player_Name", "Matches_Played", "Average", "Strike_Rate", "Batting_Impact_Score"].includes(k),
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.025, duration: 0.3 }}
      className="rounded-xl border border-white/10 bg-white/[0.03] overflow-hidden"
    >
      {/* Card header — always visible */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between gap-4 p-4 text-left hover:bg-white/[0.03] transition-colors"
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/10 text-xs font-bold text-white">
            {position}
          </div>
          <div className="min-w-0">
            <p className="truncate font-semibold text-white">{name}</p>
            <p className="text-[11px] text-muted-foreground">{matches} matches</p>
          </div>
        </div>

        {/* Stats strip */}
        <div className="hidden sm:flex items-center gap-6 shrink-0">
          <div className="text-center">
            <p className="text-[10px] uppercase text-muted-foreground">Avg</p>
            <p className="text-sm font-bold text-white">{fmt(avg)}</p>
          </div>
          <div className="text-center">
            <p className="text-[10px] uppercase text-muted-foreground">SR</p>
            <p className="text-sm font-bold text-white">{fmt(sr)}</p>
          </div>
          {wickets > 0 && (
            <div className="text-center">
              <p className="text-[10px] uppercase text-muted-foreground">Wkts</p>
              <p className="text-sm font-bold text-white">{wickets}</p>
            </div>
          )}
          {economy > 0 && (
            <div className="text-center">
              <p className="text-[10px] uppercase text-muted-foreground">Econ</p>
              <p className="text-sm font-bold text-white">{fmt(economy)}</p>
            </div>
          )}
        </div>

        <span className={`shrink-0 rounded-full border px-2.5 py-0.5 text-[11px] font-bold ${impactBg} ${impactColor}`}>
          {Math.round(impact)}
        </span>
      </button>

      {/* Expanded detail grid */}
      {expanded && (
        <div className="border-t border-white/5 p-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {extraCols.map(([key, val]) => (
            <div key={key} className="rounded-lg bg-white/[0.03] border border-white/5 p-2">
              <p className="text-[10px] uppercase tracking-wide text-muted-foreground mb-0.5">
                {key.replace(/_/g, " ")}
              </p>
              <p className="text-sm font-semibold text-white truncate">{fmt(val)}</p>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}

/* ─── Sort options ───────────────────────────────────────────────── */
type SortKey = "Batting_Impact_Score" | "Average" | "Strike_Rate" | "Wickets";
const SORT_OPTIONS: { key: SortKey; label: string }[] = [
  { key: "Batting_Impact_Score", label: "Impact" },
  { key: "Average", label: "Average" },
  { key: "Strike_Rate", label: "Strike Rate" },
  { key: "Wickets", label: "Wickets" },
];

/* ─── Main page ──────────────────────────────────────────────────── */
export default function AnalyticsPage() {
  const [tab, setTab] = useState<Tab>("players");
  const [playerSearch, setPlayerSearch] = useState("");
  const [teamSearch, setTeamSearch] = useState("");
  const [venueSearch, setVenueSearch] = useState("");
  const [playerOffset, setPlayerOffset] = useState(0);
  const [sortKey, setSortKey] = useState<SortKey>("Batting_Impact_Score");
  const [expandedPlayer, setExpandedPlayer] = useState<string | null>(null);
  const limit = 20;

  const players = usePlayers({ search: playerSearch || undefined, limit, offset: playerOffset });
  const teams = useTeams(teamSearch || undefined);
  const venues = useVenues(venueSearch || undefined);

  const [matchupBatter, setMatchupBatter] = useState("V Kohli");
  const [matchupBowler, setMatchupBowler] = useState("JJ Bumrah");

  const matchupQuery = useMatchup(matchupBatter, matchupBowler);
  const batterMatchups = usePlayerMatchups({ batter: matchupBatter, min_balls: 5, limit: 10 });
  const bowlerMatchups = usePlayerMatchups({ bowler: matchupBowler, min_balls: 5, limit: 10 });

  const tabs: { id: Tab; label: string; icon: typeof Users }[] = [
    { id: "players", label: "Players", icon: Users },
    { id: "teams", label: "Teams", icon: Shield },
    { id: "venues", label: "Venues", icon: MapPin },
    { id: "matchups", label: "Matchup Matrix", icon: Swords },
  ];

  /* Sort players client-side */
  const sortedPlayers = players.data?.players
    ? [...players.data.players].sort(
        (a, b) => Number(b[sortKey] ?? 0) - Number(a[sortKey] ?? 0),
      )
    : [];

  return (
    <div className="relative min-h-screen">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 pt-24 pb-16 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white sm:text-3xl">
              Cricket <span className="text-gradient-emerald">Analytics</span>
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Browse player, team, and venue statistics
            </p>
          </div>
          <ApiStatus />
        </div>

        {/* Tabs */}
        <div className="flex gap-1 rounded-xl bg-white/5 border border-white/10 p-1 mb-6 w-fit">
          {tabs.map((t) => {
            const Icon = t.icon;
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                  active ? "bg-emerald-500/15 text-emerald-300 shadow-sm" : "text-muted-foreground hover:text-white"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {t.label}
              </button>
            );
          })}
        </div>

        {/* ── PLAYERS TAB ── */}
        {tab === "players" && (
          <div className="space-y-4">
            {/* Search + sort */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search players…"
                  value={playerSearch}
                  onChange={(e) => { setPlayerSearch(e.target.value); setPlayerOffset(0); }}
                  className="pl-9 bg-white/5 border-white/10"
                />
              </div>
              <div className="flex gap-1 rounded-lg bg-white/5 border border-white/10 p-1">
                {SORT_OPTIONS.map((o) => (
                  <button
                    key={o.key}
                    onClick={() => setSortKey(o.key)}
                    className={`rounded px-3 py-1.5 text-xs font-medium transition-colors ${
                      sortKey === o.key ? "bg-white/10 text-white" : "text-muted-foreground hover:text-white"
                    }`}
                  >
                    {o.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Legend */}
            <div className="flex flex-wrap gap-4 text-[11px] text-muted-foreground px-1">
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-emerald-400 inline-block" /> High impact (200+)
              </span>
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-amber-400 inline-block" /> Medium impact (80+)
              </span>
              <span className="text-muted-foreground/50">· Badge = Impact Score · Position circle = Batting position</span>
            </div>

            {players.isLoading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="h-6 w-6 animate-spin text-emerald-400" />
              </div>
            ) : sortedPlayers.length === 0 ? (
              <div className="py-16 text-center text-sm text-muted-foreground">No players found</div>
            ) : (
              <div className="space-y-2">
                {sortedPlayers.map((p, i) => {
                  const name = String(p["Player_Name"] ?? i);
                  return (
                    <PlayerCard
                      key={name}
                      player={p}
                      index={i}
                      expanded={expandedPlayer === name}
                      onToggle={() => setExpandedPlayer(expandedPlayer === name ? null : name)}
                    />
                  );
                })}
              </div>
            )}

            {/* Pagination */}
            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-muted-foreground">
                {players.data
                  ? `${playerOffset + 1}–${Math.min(playerOffset + limit, players.data.total)} of ${players.data.total}`
                  : ""}
              </span>
              <div className="flex gap-2">
                <button
                  disabled={playerOffset === 0}
                  onClick={() => setPlayerOffset(Math.max(0, playerOffset - limit))}
                  className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-muted-foreground disabled:opacity-40 hover:text-white transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  disabled={!players.data || playerOffset + limit >= players.data.total}
                  onClick={() => setPlayerOffset(playerOffset + limit)}
                  className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-muted-foreground disabled:opacity-40 hover:text-white transition-colors"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── TEAMS TAB ── */}
        {tab === "teams" && (
          <div className="space-y-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search teams…"
                value={teamSearch}
                onChange={(e) => setTeamSearch(e.target.value)}
                className="pl-9 bg-white/5 border-white/10"
              />
            </div>

            {teams.isLoading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="h-6 w-6 animate-spin text-emerald-400" />
              </div>
            ) : (
              <>
                {/* Win % bar chart */}
                {teams.data && teams.data.teams.length > 0 && (
                  <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                    <div className="flex items-center gap-2 mb-4 text-sm font-semibold text-muted-foreground uppercase tracking-widest">
                      <TrendingUp className="h-4 w-4 text-emerald-400" />
                      Win Percentage by Team
                    </div>
                    <div style={{ height: Math.max(240, teams.data.teams.length * 36) }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={[...teams.data.teams]
                            .sort((a, b) => Number(b["Win_Percentage"] ?? 0) - Number(a["Win_Percentage"] ?? 0))
                            .map((t) => ({ name: String(t["Team"] ?? ""), winPct: Number(t["Win_Percentage"] ?? 0) }))}
                          layout="vertical"
                          margin={{ top: 0, right: 12, bottom: 0, left: 0 }}
                        >
                          <XAxis type="number" domain={[0, 100]} tick={{ fill: "#6b7280", fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                          <YAxis type="category" dataKey="name" tick={{ fill: "#d1d5db", fontSize: 11 }} axisLine={false} tickLine={false} width={120} />
                          <Tooltip
                            contentStyle={darkTooltip}
                            formatter={(v: number) => [`${v.toFixed(1)}%`, "Win Rate"]}
                            cursor={{ fill: "rgba(255,255,255,0.03)" }}
                          />
                          <Bar dataKey="winPct" radius={[0, 4, 4, 0]} maxBarSize={22}>
                            {teams.data.teams.map((_, i) => (
                              <Cell key={i} fill={i < 3 ? "#00c853" : i < 6 ? "#ffc107" : "#6b7280"} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Team cards */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {teams.data?.teams.map((team, i) => {
                    const name = String(team["Team"] ?? "");
                    const wins = Number(team["Wins"] ?? 0);
                    const losses = Number(team["Losses"] ?? 0);
                    const winPct = Number(team["Win_Percentage"] ?? 0);
                    const avgScore = Number(team["Average_Total"] ?? 0);
                    const chasePct = Number(team["Chasing_Win_Percentage"] ?? 0);
                    return (
                      <motion.div
                        key={name}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.04 }}
                        className="rounded-xl border border-white/10 bg-white/[0.03] p-4"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <p className="font-bold text-white truncate">{name}</p>
                          <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${winPct >= 60 ? "bg-emerald-500/15 text-emerald-400" : winPct >= 45 ? "bg-amber-500/15 text-amber-400" : "bg-white/10 text-muted-foreground"}`}>
                            {winPct.toFixed(1)}%
                          </span>
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-center">
                          <div className="rounded-lg bg-white/5 p-2">
                            <p className="text-[10px] text-muted-foreground uppercase">W</p>
                            <p className="text-sm font-bold text-emerald-400">{wins}</p>
                          </div>
                          <div className="rounded-lg bg-white/5 p-2">
                            <p className="text-[10px] text-muted-foreground uppercase">L</p>
                            <p className="text-sm font-bold text-red-400">{losses}</p>
                          </div>
                          <div className="rounded-lg bg-white/5 p-2">
                            <p className="text-[10px] text-muted-foreground uppercase">Avg</p>
                            <p className="text-sm font-bold text-white">{avgScore.toFixed(0)}</p>
                          </div>
                        </div>
                        <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
                          <span>Chase win rate</span>
                          <span className="text-white font-medium">{chasePct.toFixed(1)}%</span>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        )}

        {/* ── VENUES TAB ── */}
        {tab === "venues" && (
          <div className="space-y-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search venues…"
                value={venueSearch}
                onChange={(e) => setVenueSearch(e.target.value)}
                className="pl-9 bg-white/5 border-white/10"
              />
            </div>

            {venues.isLoading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="h-6 w-6 animate-spin text-emerald-400" />
              </div>
            ) : (
              <>
                {/* Average first-innings score bar chart */}
                {venues.data && venues.data.venues.length > 0 && (
                  <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                    <div className="flex items-center gap-2 mb-4 text-sm font-semibold text-muted-foreground uppercase tracking-widest">
                      <Target className="h-4 w-4 text-amber-400" />
                      Average First-Innings Score by Venue
                    </div>
                    <div style={{ height: Math.max(200, Math.min(venues.data.venues.length, 15) * 32) }}>
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={[...venues.data.venues]
                            .sort((a, b) => Number(b["Average_First_Innings"] ?? 0) - Number(a["Average_First_Innings"] ?? 0))
                            .slice(0, 15)
                            .map((v) => ({
                              name: String(v["Venue"] ?? "").split(",")[0].trim(), // shorten long venue names
                              avg: Number(v["Average_First_Innings"] ?? 0),
                            }))}
                          layout="vertical"
                          margin={{ top: 0, right: 12, bottom: 0, left: 0 }}
                        >
                          <XAxis type="number" domain={[0, "dataMax + 20"]} tick={{ fill: "#6b7280", fontSize: 10 }} axisLine={false} tickLine={false} />
                          <YAxis type="category" dataKey="name" tick={{ fill: "#d1d5db", fontSize: 10 }} axisLine={false} tickLine={false} width={130} />
                          <Tooltip
                            contentStyle={darkTooltip}
                            formatter={(v: number) => [v.toFixed(1), "Avg 1st Innings"]}
                            cursor={{ fill: "rgba(255,255,255,0.03)" }}
                          />
                          <Bar dataKey="avg" fill="#ffc107" radius={[0, 4, 4, 0]} maxBarSize={20} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Run rate + chasing win % bar charts side by side */}
                {venues.data && venues.data.venues.length > 0 && (
                  <div className="grid gap-6 lg:grid-cols-2">
                    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                      <div className="flex items-center gap-2 mb-4 text-sm font-semibold text-muted-foreground uppercase tracking-widest">
                        <Zap className="h-4 w-4 text-emerald-400" />
                        Average Run Rate
                      </div>
                      <div style={{ height: Math.max(180, Math.min(venues.data.venues.length, 10) * 30) }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={[...venues.data.venues]
                              .sort((a, b) => Number(b["Average_Run_Rate"] ?? 0) - Number(a["Average_Run_Rate"] ?? 0))
                              .slice(0, 10)
                              .map((v) => ({
                                name: String(v["Venue"] ?? "").split(",")[0].trim(),
                                rr: Number(v["Average_Run_Rate"] ?? 0),
                              }))}
                            layout="vertical"
                            margin={{ top: 0, right: 12, bottom: 0, left: 0 }}
                          >
                            <XAxis type="number" domain={[0, 12]} tick={{ fill: "#6b7280", fontSize: 10 }} axisLine={false} tickLine={false} />
                            <YAxis type="category" dataKey="name" tick={{ fill: "#d1d5db", fontSize: 10 }} axisLine={false} tickLine={false} width={120} />
                            <Tooltip contentStyle={darkTooltip} formatter={(v: number) => [v.toFixed(2), "Run Rate"]} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                            <Bar dataKey="rr" fill="#00c853" radius={[0, 4, 4, 0]} maxBarSize={18} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                      <div className="flex items-center gap-2 mb-4 text-sm font-semibold text-muted-foreground uppercase tracking-widest">
                        <TrendingUp className="h-4 w-4 text-indigo-400" />
                        Chasing Win %
                      </div>
                      <div style={{ height: Math.max(180, Math.min(venues.data.venues.length, 10) * 30) }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={[...venues.data.venues]
                              .sort((a, b) => Number(b["Chasing_Win_Percentage"] ?? 0) - Number(a["Chasing_Win_Percentage"] ?? 0))
                              .slice(0, 10)
                              .map((v) => ({
                                name: String(v["Venue"] ?? "").split(",")[0].trim(),
                                chPct: Number(v["Chasing_Win_Percentage"] ?? 0),
                              }))}
                            layout="vertical"
                            margin={{ top: 0, right: 12, bottom: 0, left: 0 }}
                          >
                            <XAxis type="number" domain={[0, 100]} tick={{ fill: "#6b7280", fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
                            <YAxis type="category" dataKey="name" tick={{ fill: "#d1d5db", fontSize: 10 }} axisLine={false} tickLine={false} width={120} />
                            <Tooltip contentStyle={darkTooltip} formatter={(v: number) => [`${v.toFixed(1)}%`, "Chase Win Rate"]} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                            <Bar dataKey="chPct" fill="#818cf8" radius={[0, 4, 4, 0]} maxBarSize={18} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* ── MATCHUPS TAB ── */}
        {tab === "matchups" && (
          <div className="space-y-6">
            {/* Input selectors */}
            <div className="glass-card rounded-2xl p-6 border border-white/10">
              <div className="flex items-center gap-2 mb-4 text-emerald-400">
                <Swords className="h-5 w-5" />
                <h2 className="text-base font-bold uppercase tracking-wider text-white">
                  Tactical Head-to-Head Clash Matrix
                </h2>
              </div>
              <p className="text-xs text-muted-foreground mb-4">
                Analyze individual batter vs bowler matchups across 280,000+ historical balls to identify tactical edges, strike rates, dismissals, and boundary frequencies.
              </p>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-1.5">
                    Batter Name
                  </label>
                  <Input
                    placeholder="e.g. V Kohli, RG Sharma, MS Dhoni, DA Warner..."
                    value={matchupBatter}
                    onChange={(e) => setMatchupBatter(e.target.value)}
                    className="bg-white/5 border-white/10"
                  />
                  {/* Quick Select */}
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {["V Kohli", "RG Sharma", "MS Dhoni", "AB de Villiers", "DA Warner", "KL Rahul"].map((b) => (
                      <button
                        key={b}
                        onClick={() => setMatchupBatter(b)}
                        className={`text-[11px] px-2.5 py-0.5 rounded-full border transition-colors ${
                          matchupBatter === b
                            ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                            : "bg-white/5 border-white/10 text-muted-foreground hover:text-white"
                        }`}
                      >
                        {b}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-1.5">
                    Bowler Name
                  </label>
                  <Input
                    placeholder="e.g. JJ Bumrah, SP Narine, Rashid Khan, B Kumar..."
                    value={matchupBowler}
                    onChange={(e) => setMatchupBowler(e.target.value)}
                    className="bg-white/5 border-white/10"
                  />
                  {/* Quick Select */}
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {["JJ Bumrah", "SP Narine", "Rashid Khan", "B Kumar", "YS Chahal", "R Ashwin"].map((bw) => (
                      <button
                        key={bw}
                        onClick={() => setMatchupBowler(bw)}
                        className={`text-[11px] px-2.5 py-0.5 rounded-full border transition-colors ${
                          matchupBowler === bw
                            ? "bg-amber-500/20 border-amber-500/40 text-amber-300"
                            : "bg-white/5 border-white/10 text-muted-foreground hover:text-white"
                        }`}
                      >
                        {bw}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Head-to-Head Clash Card */}
            {matchupQuery.isLoading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
              </div>
            ) : matchupQuery.data?.found && matchupQuery.data.matchup ? (
              <div className="rounded-2xl border border-emerald-500/20 bg-gradient-to-r from-emerald-950/20 via-zinc-900/60 to-black p-6">
                <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-4 mb-5">
                  <div>
                    <span className="text-xs uppercase tracking-widest text-emerald-400 font-semibold">
                      Direct Head-to-Head
                    </span>
                    <h3 className="text-xl font-bold text-white mt-0.5">
                      {matchupQuery.data.matchup.Batter}{" "}
                      <span className="text-amber-400 text-sm font-normal">vs</span>{" "}
                      {matchupQuery.data.matchup.Bowler}
                    </h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                        matchupQuery.data.matchup.Dismissals >= 2 || matchupQuery.data.matchup.Strike_Rate < 110
                          ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                          : matchupQuery.data.matchup.Strike_Rate > 150
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      }`}
                    >
                      {matchupQuery.data.matchup.Dismissals >= 2
                        ? `Bowler Advantage (${matchupQuery.data.matchup.Dismissals} Outs)`
                        : matchupQuery.data.matchup.Strike_Rate > 150
                        ? `Batter Dominates (${matchupQuery.data.matchup.Strike_Rate} SR)`
                        : "Even Matchup"}
                    </span>
                  </div>
                </div>

                {/* 4 Key Stat Gauges */}
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-5">
                  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-center">
                    <p className="text-xs text-muted-foreground uppercase">Runs / Balls</p>
                    <p className="text-2xl font-bold text-white mt-1">
                      {matchupQuery.data.matchup.Runs_Scored}
                      <span className="text-sm font-normal text-muted-foreground">
                        {" "}({matchupQuery.data.matchup.Balls_Faced}b)
                      </span>
                    </p>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-center">
                    <p className="text-xs text-muted-foreground uppercase">Strike Rate</p>
                    <p
                      className={`text-2xl font-bold mt-1 ${
                        matchupQuery.data.matchup.Strike_Rate >= 140
                          ? "text-emerald-400"
                          : matchupQuery.data.matchup.Strike_Rate <= 110
                          ? "text-rose-400"
                          : "text-amber-400"
                      }`}
                    >
                      {matchupQuery.data.matchup.Strike_Rate}
                    </p>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-center">
                    <p className="text-xs text-muted-foreground uppercase">Dismissals</p>
                    <p className="text-2xl font-bold text-rose-400 mt-1">
                      {matchupQuery.data.matchup.Dismissals}
                    </p>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 text-center">
                    <p className="text-xs text-muted-foreground uppercase">Dot Ball %</p>
                    <p className="text-2xl font-bold text-white mt-1">
                      {matchupQuery.data.matchup.Dot_Percentage}%
                    </p>
                  </div>
                </div>

                {/* Boundary Breakdowns */}
                <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-zinc-300 bg-black/40 rounded-xl p-3.5 border border-white/5">
                  <div className="flex items-center gap-4">
                    <span>
                      <strong className="text-emerald-400">{matchupQuery.data.matchup.Fours}</strong> Fours
                    </span>
                    <span>
                      <strong className="text-amber-400">{matchupQuery.data.matchup.Sixes}</strong> Sixes
                    </span>
                    <span>
                      <strong className="text-white">{matchupQuery.data.matchup.Dot_Balls}</strong> Dots
                    </span>
                  </div>
                  <div>
                    Boundary Frequency:{" "}
                    <strong className="text-emerald-400">{matchupQuery.data.matchup.Boundary_Percentage}%</strong>
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-8 text-center text-muted-foreground">
                <p className="text-sm">
                  {matchupQuery.data?.message || "Select a batter and bowler above to compute head-to-head metrics."}
                </p>
              </div>
            )}

            {/* Related Matchups Tables */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {/* Batter's Top Bowlers */}
              <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-5">
                <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                  <Crosshair className="h-4 w-4 text-emerald-400" />
                  Top Matchups for {matchupBatter}
                </h3>
                {batterMatchups.isLoading ? (
                  <div className="py-8 text-center">
                    <Loader2 className="h-5 w-5 animate-spin mx-auto text-emerald-400" />
                  </div>
                ) : (batterMatchups.data?.matchups ?? []).length === 0 ? (
                  <p className="text-xs text-muted-foreground py-4 text-center">No recorded matchups</p>
                ) : (
                  <div className="space-y-2">
                    {batterMatchups.data?.matchups.map((m, i) => (
                      <div
                        key={i}
                        onClick={() => setMatchupBowler(m.Bowler)}
                        className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.06] cursor-pointer transition-colors border border-white/5 text-xs"
                      >
                        <div>
                          <span className="font-semibold text-white">{m.Bowler}</span>
                          <span className="text-[11px] text-muted-foreground ml-2">
                            {m.Runs_Scored} runs ({m.Balls_Faced}b)
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-emerald-400">{m.Strike_Rate} SR</span>
                          <span className="font-mono text-rose-400">{m.Dismissals} W</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Bowler's Top Batters */}
              <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-5">
                <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                  <Flame className="h-4 w-4 text-amber-400" />
                  Top Matchups for {matchupBowler}
                </h3>
                {bowlerMatchups.isLoading ? (
                  <div className="py-8 text-center">
                    <Loader2 className="h-5 w-5 animate-spin mx-auto text-amber-400" />
                  </div>
                ) : (bowlerMatchups.data?.matchups ?? []).length === 0 ? (
                  <p className="text-xs text-muted-foreground py-4 text-center">No recorded matchups</p>
                ) : (
                  <div className="space-y-2">
                    {bowlerMatchups.data?.matchups.map((m, i) => (
                      <div
                        key={i}
                        onClick={() => setMatchupBatter(m.Batter)}
                        className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.06] cursor-pointer transition-colors border border-white/5 text-xs"
                      >
                        <div>
                          <span className="font-semibold text-white">{m.Batter}</span>
                          <span className="text-[11px] text-muted-foreground ml-2">
                            {m.Dismissals} dismissals ({m.Balls_Faced}b)
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-amber-400">{m.Runs_Scored} R</span>
                          <span className="font-mono text-rose-400">{m.Dot_Percentage}% Dots</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
