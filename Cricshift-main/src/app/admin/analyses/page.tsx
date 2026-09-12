"use client";

import { useState, useMemo } from "react";
import { useAdminPredictions, useAdminHistorical } from "@/lib/api/admin";
import { BarChart2, FileText, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function fmt(iso: string) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", hour12: true,
  });
}

function momentumBadge(cls: string) {
  if (cls === "Positive") return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
  if (cls === "Negative") return "bg-red-500/10 text-red-400 border-red-500/20";
  return "bg-zinc-700/10 text-zinc-400 border-zinc-700/20";
}

function typeBadge(t: string) {
  if (t === "win")      return "bg-blue-500/10 text-blue-300 border-blue-500/20";
  if (t === "momentum") return "bg-purple-500/10 text-purple-300 border-purple-500/20";
  return "bg-zinc-700/10 text-zinc-400 border-zinc-700/20";
}

/* ── Predictions tab ──────────────────────────────────────────────── */
function PredictionsTable() {
  const [search, setSearch] = useState("");
  const { data: preds = [], isLoading } = useAdminPredictions(500);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    if (!q) return preds;
    return preds.filter(
      (p) =>
        p.batting_team.toLowerCase().includes(q) ||
        p.bowling_team.toLowerCase().includes(q) ||
        p.venue.toLowerCase().includes(q) ||
        p.predicted_winner.toLowerCase().includes(q),
    );
  }, [preds, search]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <p className="text-sm text-zinc-400">{preds.length} total predictions</p>
        <div className="relative max-w-xs w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500 pointer-events-none" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search team, venue…"
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-zinc-900 border border-zinc-700 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-blue-500/50"
          />
        </div>
      </div>
      <Card className="bg-zinc-950 border-zinc-800">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-zinc-800 hover:bg-transparent">
                <TableHead className="text-zinc-400 pl-5">Type</TableHead>
                <TableHead className="text-zinc-400">Teams</TableHead>
                <TableHead className="text-zinc-400">Over / Score</TableHead>
                <TableHead className="text-zinc-400">Momentum</TableHead>
                <TableHead className="text-zinc-400 text-right">Win %</TableHead>
                <TableHead className="text-zinc-400">Predicted Winner</TableHead>
                <TableHead className="text-zinc-400 pr-5">Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                [...Array(5)].map((_, i) => (
                  <TableRow key={i} className="border-zinc-800">
                    {[...Array(7)].map((_, j) => (
                      <TableCell key={j} className="pl-5">
                        <div className="h-4 rounded bg-zinc-800 animate-pulse w-20" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-zinc-600 py-14">
                    {preds.length === 0
                      ? "No predictions yet. Run a prediction from the Dashboard."
                      : "No results match your search."}
                  </TableCell>
                </TableRow>
              ) : filtered.map((p) => (
                <TableRow key={p.id} className="border-zinc-800 hover:bg-zinc-900/40 text-white">
                  <TableCell className="pl-5">
                    <Badge variant="outline" className={`text-xs capitalize ${typeBadge(p.type)}`}>
                      {p.type}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <p className="text-sm font-medium">{p.batting_team}</p>
                    <p className="text-xs text-zinc-500">vs {p.bowling_team}</p>
                  </TableCell>
                  <TableCell className="text-sm text-zinc-300 tabular-nums">
                    Ov {p.current_over} — {p.current_score}/{p.current_wickets}
                    {p.target > 0 && (
                      <span className="text-zinc-500 text-xs ml-1">T:{p.target}</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {p.momentum_class ? (
                      <Badge variant="outline" className={`text-xs ${momentumBadge(p.momentum_class)}`}>
                        {p.momentum_class}
                      </Badge>
                    ) : <span className="text-zinc-600 text-xs">—</span>}
                  </TableCell>
                  <TableCell className="text-right tabular-nums font-bold text-emerald-400 text-sm">
                    {p.win_prob_batting.toFixed(1)}%
                  </TableCell>
                  <TableCell className="text-sm text-zinc-200 max-w-[140px] truncate">
                    {p.predicted_winner || "—"}
                  </TableCell>
                  <TableCell className="text-xs text-zinc-500 pr-5">{fmt(p.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {filtered.length > 0 && (
            <div className="px-5 py-3 border-t border-zinc-800 text-xs text-zinc-600">
              Showing {filtered.length} of {preds.length} predictions
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/* ── Historical tab ───────────────────────────────────────────────── */
function HistoricalTable() {
  const [search, setSearch] = useState("");
  const { data: hist = [], isLoading } = useAdminHistorical(500);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    if (!q) return hist;
    return hist.filter(
      (h) =>
        h.filename.toLowerCase().includes(q) ||
        h.batting_team.toLowerCase().includes(q) ||
        h.bowling_team.toLowerCase().includes(q) ||
        h.venue.toLowerCase().includes(q),
    );
  }, [hist, search]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <p className="text-sm text-zinc-400">{hist.length} total uploads</p>
        <div className="relative max-w-xs w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500 pointer-events-none" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search file, team, venue…"
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-zinc-900 border border-zinc-700 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-indigo-500/50"
          />
        </div>
      </div>
      <Card className="bg-zinc-950 border-zinc-800">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-zinc-800 hover:bg-transparent">
                <TableHead className="text-zinc-400 pl-5">Filename</TableHead>
                <TableHead className="text-zinc-400">Teams</TableHead>
                <TableHead className="text-zinc-400">Venue</TableHead>
                <TableHead className="text-zinc-400 text-center">Overs</TableHead>
                <TableHead className="text-zinc-400 text-center">Shifts</TableHead>
                <TableHead className="text-zinc-400 text-right">Size</TableHead>
                <TableHead className="text-zinc-400 pr-5">Uploaded</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                [...Array(4)].map((_, i) => (
                  <TableRow key={i} className="border-zinc-800">
                    {[...Array(7)].map((_, j) => (
                      <TableCell key={j} className="pl-5">
                        <div className="h-4 rounded bg-zinc-800 animate-pulse w-20" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-zinc-600 py-14">
                    {hist.length === 0
                      ? "No historical CSVs uploaded yet. Go to the Historical page to upload one."
                      : "No results match your search."}
                  </TableCell>
                </TableRow>
              ) : filtered.map((h) => (
                <TableRow key={h.id} className="border-zinc-800 hover:bg-zinc-900/40 text-white">
                  <TableCell className="pl-5">
                    <p className="font-medium text-sm max-w-[180px] truncate">{h.filename}</p>
                    <p className="text-xs text-zinc-600 font-mono">{h.analysis_id}</p>
                  </TableCell>
                  <TableCell>
                    <p className="text-sm">{h.batting_team}</p>
                    <p className="text-xs text-zinc-500">vs {h.bowling_team}</p>
                  </TableCell>
                  <TableCell className="text-sm text-zinc-300 max-w-[140px] truncate">
                    {h.venue || "—"}
                  </TableCell>
                  <TableCell className="text-center tabular-nums text-zinc-200">
                    {h.timeline_length}
                  </TableCell>
                  <TableCell className="text-center tabular-nums">
                    <span className={`font-semibold text-sm ${
                      h.turning_points_count > 3 ? "text-amber-400" : "text-zinc-300"
                    }`}>
                      {h.turning_points_count}
                    </span>
                  </TableCell>
                  <TableCell className="text-right text-xs text-zinc-400 tabular-nums">
                    {h.file_size_kb.toFixed(1)} KB
                  </TableCell>
                  <TableCell className="text-xs text-zinc-500 pr-5">{fmt(h.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {filtered.length > 0 && (
            <div className="px-5 py-3 border-t border-zinc-800 text-xs text-zinc-600">
              Showing {filtered.length} of {hist.length} analyses
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════ */
export default function AdminAnalysesPage() {
  const [tab, setTab] = useState<"predictions" | "historical">("predictions");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <BarChart2 className="h-5 w-5 text-blue-400" />
          Analyses &amp; Predictions
        </h1>
        <p className="text-zinc-400 text-sm mt-0.5">
          All ML prediction calls and historical CSV analyses in one place.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl bg-zinc-900 p-1 w-fit border border-zinc-800">
        {(["predictions", "historical"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t
                ? "bg-zinc-800 text-white"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {t === "predictions"
              ? <><BarChart2 className="h-4 w-4" /> Predictions</>
              : <><FileText className="h-4 w-4" /> Historical Uploads</>}
          </button>
        ))}
      </div>

      {tab === "predictions" ? <PredictionsTable /> : <HistoricalTable />}
    </div>
  );
}
