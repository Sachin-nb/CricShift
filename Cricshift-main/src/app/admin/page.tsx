"use client";

import Link from "next/link";
import {
  useAdminStats,
  useAdminMatches,
  useAdminSimulations,
  useAdminHistorical,
  useAdminPredictions,
} from "@/lib/api/admin";
import {
  Activity, Zap, BarChart2, RefreshCw, FileText, ChevronRight,
} from "lucide-react";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

/* ── helpers ── */
function fmt(iso: string) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit", month: "short",
    hour: "2-digit", minute: "2-digit", hour12: true,
  });
}

function momentumBadge(cls: string) {
  const map: Record<string, string> = {
    Positive: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    Neutral:  "bg-zinc-500/10  text-zinc-300    border-zinc-500/20",
    Negative: "bg-red-500/10   text-red-400     border-red-500/20",
  };
  return map[cls] ?? "bg-zinc-700/10 text-zinc-400 border-zinc-700/20";
}

/* ── KPI card ── */
const ACCENTS: Record<string, { bar: string; text: string; glow: string }> = {
  emerald: { bar: "from-emerald-400 to-emerald-600", text: "text-emerald-400", glow: "group-hover:shadow-[0_0_40px_-12px_rgba(0,200,83,0.4)]" },
  blue:    { bar: "from-blue-400 to-blue-600",       text: "text-blue-400",    glow: "group-hover:shadow-[0_0_40px_-12px_rgba(59,130,246,0.4)]" },
  amber:   { bar: "from-amber-400 to-amber-600",     text: "text-amber-400",   glow: "group-hover:shadow-[0_0_40px_-12px_rgba(255,193,7,0.4)]" },
  indigo:  { bar: "from-indigo-400 to-indigo-600",   text: "text-indigo-400",  glow: "group-hover:shadow-[0_0_40px_-12px_rgba(129,140,248,0.4)]" },
};

function StatCard({
  label, total, today, icon: Icon, accent, href,
}: {
  label: string; total: number | string; today: number | string;
  icon: React.ElementType; accent: keyof typeof ACCENTS; href: string;
}) {
  const a = ACCENTS[accent];
  return (
    <Link href={href}>
      <div className={`glass-card glass-card-hover group relative h-full overflow-hidden rounded-2xl p-5 ${a.glow}`}>
        {/* Top accent bar */}
        <div className={`pointer-events-none absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r ${a.bar}`} />
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-400">{label}</p>
          <div className={`grid h-9 w-9 place-items-center rounded-xl border border-white/10 bg-white/5 ${a.text}`}>
            <Icon className="h-4 w-4" />
          </div>
        </div>
        <div className="mt-4 text-3xl font-bold tabular-nums text-white">
          {total ?? <span className="text-xl text-zinc-600">—</span>}
        </div>
        <p className="mt-1 text-xs text-zinc-500">
          <span className={`font-semibold ${a.text}`}>+{today ?? 0}</span> today
        </p>
      </div>
    </Link>
  );
}

/* ── section card wrapper ── */
function SectionCard({
  title, href, children,
}: { title: string; href: string; children: React.ReactNode }) {
  return (
    <div className="glass-card overflow-hidden rounded-2xl">
      <div className="flex items-center justify-between border-b border-white/5 px-5 py-3.5">
        <p className="text-sm font-semibold text-zinc-200">{title}</p>
        <Link
          href={href}
          className="flex items-center gap-1 text-xs text-zinc-500 transition-colors hover:text-emerald-400"
        >
          View all <ChevronRight className="h-3 w-3" />
        </Link>
      </div>
      <div className="overflow-x-auto">{children}</div>
    </div>
  );
}

const emptyRow = (msg: string) => (
  <TableRow>
    <TableCell colSpan={3} className="py-10 pl-5 text-center text-sm text-zinc-600">
      {msg}
    </TableCell>
  </TableRow>
);

const thBase = "text-[11px] uppercase tracking-wider text-zinc-500";
const rowBase = "border-white/5 transition-colors hover:bg-white/[0.03]";

/* ═══════════════════════════════════════════════════════════════════ */
export default function AdminDashboard() {
  const { data: stats } = useAdminStats();
  const { data: matches = [] }  = useAdminMatches(5);
  const { data: sims    = [] }  = useAdminSimulations(5);
  const { data: hist    = [] }  = useAdminHistorical(5);
  const { data: preds   = [] }  = useAdminPredictions(5);

  return (
    <div className="space-y-10">
      {/* ── Page header ── */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-400">
            Admin Console
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">
            Activity <span className="text-gradient-emerald">Overview</span>
          </h1>
          <p className="mt-1.5 text-sm text-zinc-400">
            Real-time activity across the CricShift analytics engine.
          </p>
        </div>
        <span className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-zinc-400">
          <RefreshCw className="h-3 w-3" /> Auto-refreshes every 30s
        </span>
      </div>

      {/* ── KPI cards ── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Live Matches Seen"
          total={stats?.total_live_matches ?? "—"}
          today={stats?.live_matches_today ?? 0}
          icon={Activity} accent="emerald" href="/admin/matches"
        />
        <StatCard
          label="Predictions Made"
          total={stats?.total_predictions ?? "—"}
          today={stats?.predictions_today ?? 0}
          icon={BarChart2} accent="blue" href="/admin/analyses"
        />
        <StatCard
          label="Simulations Run"
          total={stats?.total_simulations ?? "—"}
          today={stats?.simulations_today ?? 0}
          icon={Zap} accent="amber" href="/admin/simulations"
        />
        <StatCard
          label="Historical Analyses"
          total={stats?.total_historical ?? "—"}
          today={stats?.historical_today ?? 0}
          icon={FileText} accent="indigo" href="/admin/analyses"
        />
      </div>

      {/* ── Recent activity grid ── */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent live matches */}
        <SectionCard title="Recent Live Matches" href="/admin/matches">
          <Table>
            <TableHeader>
              <TableRow className="border-white/5 hover:bg-transparent">
                <TableHead className={`${thBase} pl-5`}>Match</TableHead>
                <TableHead className={thBase}>Format</TableHead>
                <TableHead className={`${thBase} pr-5 text-right`}>Last Seen</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {matches.length === 0 ? emptyRow("No matches recorded yet — visit the Live page to start tracking.")
                : matches.map((m) => (
                  <TableRow key={m.id} className={rowBase}>
                    <TableCell className="pl-5">
                      <p className="text-sm font-medium text-white">
                        {m.team_a} <span className="font-normal text-zinc-500">vs</span> {m.team_b}
                      </p>
                      <p className="max-w-[180px] truncate text-xs text-zinc-500">{m.series || m.venue}</p>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="border-white/10 bg-white/5 text-xs text-zinc-300">
                        {m.match_format}
                      </Badge>
                    </TableCell>
                    <TableCell className="pr-5 text-right text-xs text-zinc-500">
                      {fmt(m.last_seen_at)}
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </SectionCard>

        {/* Recent simulations */}
        <SectionCard title="Recent Simulations" href="/admin/simulations">
          <Table>
            <TableHeader>
              <TableRow className="border-white/5 hover:bg-transparent">
                <TableHead className={`${thBase} pl-5`}>Scenario</TableHead>
                <TableHead className={thBase}>Win Δ</TableHead>
                <TableHead className={`${thBase} pr-5 text-right`}>Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sims.length === 0 ? emptyRow("No simulations yet — try the What-If Simulator.")
                : sims.map((s) => {
                  const delta = s.modified_win_prob - s.original_win_prob;
                  return (
                    <TableRow key={s.id} className={rowBase}>
                      <TableCell className="pl-5">
                        <p className="max-w-[160px] truncate text-sm font-medium text-white">
                          {s.scenario_name || "Custom Scenario"}
                        </p>
                        <p className="text-xs text-zinc-500">{s.batting_team} vs {s.bowling_team}</p>
                      </TableCell>
                      <TableCell>
                        <span className={`text-sm font-bold tabular-nums ${
                          delta > 0 ? "text-emerald-400" : delta < 0 ? "text-red-400" : "text-zinc-400"
                        }`}>
                          {delta >= 0 ? "+" : ""}{delta.toFixed(1)}%
                        </span>
                      </TableCell>
                      <TableCell className="pr-5 text-right text-xs text-zinc-500">
                        {fmt(s.created_at)}
                      </TableCell>
                    </TableRow>
                  );
                })}
            </TableBody>
          </Table>
        </SectionCard>

        {/* Recent predictions */}
        <SectionCard title="Recent Predictions" href="/admin/analyses">
          <Table>
            <TableHeader>
              <TableRow className="border-white/5 hover:bg-transparent">
                <TableHead className={`${thBase} pl-5`}>Match State</TableHead>
                <TableHead className={thBase}>Momentum</TableHead>
                <TableHead className={`${thBase} pr-5 text-right`}>Win %</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {preds.length === 0 ? emptyRow("No predictions yet — visit the Dashboard to run one.")
                : preds.map((p) => (
                  <TableRow key={p.id} className={rowBase}>
                    <TableCell className="pl-5">
                      <p className="text-sm font-medium text-white">
                        {p.batting_team} <span className="text-xs text-zinc-500">Ov {p.current_over}</span>
                      </p>
                      <p className="text-xs text-zinc-500">
                        {p.current_score}/{p.current_wickets}{p.target > 0 ? ` — T: ${p.target}` : ""}
                      </p>
                    </TableCell>
                    <TableCell>
                      {p.momentum_class ? (
                        <Badge variant="outline" className={`text-xs ${momentumBadge(p.momentum_class)}`}>
                          {p.momentum_class}
                        </Badge>
                      ) : <span className="text-xs text-zinc-600">—</span>}
                    </TableCell>
                    <TableCell className="pr-5 text-right tabular-nums">
                      <span className="text-sm font-bold text-emerald-400">
                        {p.win_prob_batting.toFixed(1)}%
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </SectionCard>

        {/* Recent historical analyses */}
        <SectionCard title="Recent Historical Analyses" href="/admin/analyses">
          <Table>
            <TableHeader>
              <TableRow className="border-white/5 hover:bg-transparent">
                <TableHead className={`${thBase} pl-5`}>File / Match</TableHead>
                <TableHead className={thBase}>Overs</TableHead>
                <TableHead className={`${thBase} pr-5 text-right`}>Uploaded</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {hist.length === 0 ? emptyRow("No historical CSVs uploaded yet.")
                : hist.map((h) => (
                  <TableRow key={h.id} className={rowBase}>
                    <TableCell className="pl-5">
                      <p className="max-w-[160px] truncate text-sm font-medium text-white">{h.filename}</p>
                      <p className="text-xs text-zinc-500">{h.batting_team} vs {h.bowling_team}</p>
                    </TableCell>
                    <TableCell className="text-sm tabular-nums text-zinc-300">
                      {h.timeline_length}
                      <span className="ml-1 text-xs text-zinc-600">({h.turning_points_count} shifts)</span>
                    </TableCell>
                    <TableCell className="pr-5 text-right text-xs text-zinc-500">
                      {fmt(h.created_at)}
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </SectionCard>
      </div>
    </div>
  );
}
