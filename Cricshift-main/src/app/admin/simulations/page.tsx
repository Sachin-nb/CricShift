"use client";

import { useState, useMemo } from "react";
import { useAdminSimulations } from "@/lib/api/admin";
import { Zap, Search, ChevronDown, ChevronUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Card, CardContent } from "@/components/ui/card";

function fmt(iso: string) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", hour12: true,
  });
}

function momentumColor(cls: string) {
  if (cls === "Positive") return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
  if (cls === "Negative") return "bg-red-500/10 text-red-400 border-red-500/20";
  return "bg-zinc-700/10 text-zinc-400 border-zinc-700/20";
}

function DeltaBadge({ value }: { value: number }) {
  const sign = value > 0 ? "+" : "";
  const color = value > 5 ? "text-emerald-400" : value < -5 ? "text-red-400" : "text-zinc-300";
  return (
    <span className={`font-bold tabular-nums text-sm ${color}`}>
      {sign}{value.toFixed(1)}%
    </span>
  );
}

function ModificationsCell({ json }: { json: string }) {
  let obj: Record<string, any> = {};
  try { obj = JSON.parse(json); } catch { obj = {}; }
  const entries = Object.entries(obj);
  if (entries.length === 0) return <span className="text-zinc-600 text-xs">—</span>;
  return (
    <div className="flex flex-col gap-0.5">
      {entries.map(([k, v]) => (
        <span key={k} className="text-xs">
          <span className="text-zinc-500">{k}:</span>{" "}
          <span className="text-amber-300 font-mono">{String(v)}</span>
        </span>
      ))}
    </div>
  );
}

function ExpandableRow({ sim }: { sim: any }) {
  const [open, setOpen] = useState(false);
  const delta = sim.modified_win_prob - sim.original_win_prob;

  return (
    <>
      <TableRow
        className="border-zinc-800 hover:bg-zinc-900/40 text-white cursor-pointer"
        onClick={() => setOpen((v) => !v)}
      >
        <TableCell className="pl-5">
          <div className="flex flex-col">
            <span className="font-semibold text-sm">{sim.scenario_name || "Custom Scenario"}</span>
            <span className="text-xs text-zinc-500">
              {sim.batting_team} vs {sim.bowling_team}
            </span>
          </div>
        </TableCell>
        <TableCell className="text-sm text-zinc-300 tabular-nums">
          {sim.current_score}/{sim.current_wickets}
          <span className="text-zinc-600 ml-1 text-xs">Ov {sim.current_over}</span>
          {sim.target > 0 && (
            <span className="text-zinc-600 ml-1 text-xs">T:{sim.target}</span>
          )}
        </TableCell>
        <TableCell><DeltaBadge value={delta} /></TableCell>
        <TableCell className="text-xs text-zinc-400 text-center">
          <span className="text-zinc-500">{sim.original_win_prob.toFixed(1)}%</span>
          {" → "}
          <span className="text-white">{sim.modified_win_prob.toFixed(1)}%</span>
        </TableCell>
        <TableCell>
          <div className="flex items-center gap-2">
            {sim.original_momentum && (
              <Badge variant="outline" className={`text-xs ${momentumColor(sim.original_momentum)}`}>
                {sim.original_momentum}
              </Badge>
            )}
            {sim.original_momentum !== sim.modified_momentum && sim.modified_momentum && (
              <>
                <span className="text-zinc-600 text-xs">→</span>
                <Badge variant="outline" className={`text-xs ${momentumColor(sim.modified_momentum)}`}>
                  {sim.modified_momentum}
                </Badge>
              </>
            )}
          </div>
        </TableCell>
        <TableCell className="text-xs text-zinc-500 pr-5">{fmt(sim.created_at)}</TableCell>
        <TableCell className="pr-5">
          {open
            ? <ChevronUp className="h-4 w-4 text-zinc-500" />
            : <ChevronDown className="h-4 w-4 text-zinc-500" />}
        </TableCell>
      </TableRow>

      {open && (
        <TableRow className="border-zinc-800 bg-zinc-900/30">
          <TableCell colSpan={7} className="pl-5 pr-5 py-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
                  Modifications Applied
                </p>
                <ModificationsCell json={sim.modifications_json} />
              </div>
              {sim.explanation && (
                <div>
                  <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
                    AI Explanation
                  </p>
                  <p className="text-sm text-zinc-300 leading-relaxed">{sim.explanation}</p>
                </div>
              )}
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}

export default function AdminSimulationsPage() {
  const [search, setSearch] = useState("");
  const { data: sims = [], isLoading } = useAdminSimulations(500);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    if (!q) return sims;
    return sims.filter(
      (s) =>
        s.scenario_name.toLowerCase().includes(q) ||
        s.batting_team.toLowerCase().includes(q) ||
        s.bowling_team.toLowerCase().includes(q),
    );
  }, [sims, search]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Zap className="h-5 w-5 text-amber-400" />
            What-If Simulations Log
          </h1>
          <p className="text-zinc-400 text-sm mt-0.5">
            Every scenario run through the simulation engine — {sims.length} total.
            Click a row to expand details.
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500 pointer-events-none" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search scenario, team…"
          className="w-full pl-9 pr-4 py-2 rounded-lg bg-zinc-900 border border-zinc-700 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-amber-500/50"
        />
      </div>

      {/* Table */}
      <Card className="bg-zinc-950 border-zinc-800">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-zinc-800 hover:bg-transparent">
                <TableHead className="text-zinc-400 pl-5">Scenario</TableHead>
                <TableHead className="text-zinc-400">Match State</TableHead>
                <TableHead className="text-zinc-400">Win Δ</TableHead>
                <TableHead className="text-zinc-400 text-center">Win Prob</TableHead>
                <TableHead className="text-zinc-400">Momentum</TableHead>
                <TableHead className="text-zinc-400 pr-5">Time</TableHead>
                <TableHead className="w-8" />
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
                  <TableCell colSpan={7} className="text-center text-zinc-600 py-16">
                    {sims.length === 0
                      ? "No simulations yet. Use the What-If Simulator on the live or historical pages."
                      : "No results match your search."}
                  </TableCell>
                </TableRow>
              ) : filtered.map((s) => <ExpandableRow key={s.id} sim={s} />)}
            </TableBody>
          </Table>
          {filtered.length > 0 && (
            <div className="px-5 py-3 border-t border-zinc-800 text-xs text-zinc-600">
              Showing {filtered.length} of {sims.length} simulations
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
