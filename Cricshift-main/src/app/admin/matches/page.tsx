"use client";

import { useState, useMemo } from "react";
import { useAdminMatches } from "@/lib/api/admin";
import { Activity, Search, RefreshCw } from "lucide-react";
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

export default function AdminMatchesPage() {
  const [search, setSearch] = useState("");
  const [formatFilter, setFormatFilter] = useState("All");
  const { data: matches = [], isLoading, dataUpdatedAt } = useAdminMatches(500);

  const formats = useMemo(() => {
    const s = new Set(matches.map((m) => m.match_format).filter(Boolean));
    return ["All", ...Array.from(s)];
  }, [matches]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return matches.filter((m) => {
      const matchesSearch =
        !q ||
        m.team_a.toLowerCase().includes(q) ||
        m.team_b.toLowerCase().includes(q) ||
        m.series.toLowerCase().includes(q) ||
        m.venue.toLowerCase().includes(q) ||
        m.match_id.toString().includes(q);
      const matchesFormat = formatFilter === "All" || m.match_format === formatFilter;
      return matchesSearch && matchesFormat;
    });
  }, [matches, search, formatFilter]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="h-5 w-5 text-emerald-400" />
            Live Matches Log
          </h1>
          <p className="text-zinc-400 text-sm mt-0.5">
            Every live match observed by the engine — {matches.length} total
          </p>
        </div>
        <span className="flex items-center gap-1.5 text-xs text-zinc-600">
          <RefreshCw className="h-3 w-3" />
          {dataUpdatedAt ? `Updated ${fmt(new Date(dataUpdatedAt).toISOString())}` : "Loading…"}
        </span>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500 pointer-events-none" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search teams, series, venue…"
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-zinc-900 border border-zinc-700 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-emerald-500/50"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {formats.map((f) => (
            <button
              key={f}
              onClick={() => setFormatFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                formatFilter === f
                  ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-400"
                  : "bg-zinc-900 border-zinc-700 text-zinc-400 hover:border-zinc-500"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <Card className="bg-zinc-950 border-zinc-800">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="border-zinc-800 hover:bg-transparent">
                <TableHead className="text-zinc-400 pl-5 w-[40%]">Match</TableHead>
                <TableHead className="text-zinc-400">Series / Venue</TableHead>
                <TableHead className="text-zinc-400">Format</TableHead>
                <TableHead className="text-zinc-400 text-center">Fetches</TableHead>
                <TableHead className="text-zinc-400">First Seen</TableHead>
                <TableHead className="text-zinc-400 pr-5">Last Seen</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                [...Array(6)].map((_, i) => (
                  <TableRow key={i} className="border-zinc-800">
                    {[...Array(6)].map((_, j) => (
                      <TableCell key={j} className="pl-5">
                        <div className="h-4 rounded bg-zinc-800 animate-pulse w-24" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-zinc-600 py-16">
                    {matches.length === 0
                      ? "No matches recorded yet. Visit the Live page to start fetching matches."
                      : "No matches match your search."}
                  </TableCell>
                </TableRow>
              ) : filtered.map((m) => (
                <TableRow key={m.id} className="border-zinc-800 hover:bg-zinc-900/40 text-white">
                  <TableCell className="pl-5">
                    <div className="flex flex-col">
                      <span className="font-semibold text-sm">
                        {m.team_a} <span className="text-zinc-500 font-normal">vs</span> {m.team_b}
                      </span>
                      <span className="text-xs text-zinc-600 font-mono">ID: {m.match_id}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm text-zinc-300 max-w-[200px]">
                    <p className="truncate">{m.series || "—"}</p>
                    <p className="text-xs text-zinc-500 truncate">{m.venue || "—"}</p>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="border-zinc-700 text-zinc-300 text-xs">
                      {m.match_format || "—"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-center tabular-nums text-zinc-300">
                    {m.fetch_count}
                  </TableCell>
                  <TableCell className="text-xs text-zinc-500">{fmt(m.first_seen_at)}</TableCell>
                  <TableCell className="text-xs text-zinc-400 pr-5">{fmt(m.last_seen_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {filtered.length > 0 && (
            <div className="px-5 py-3 border-t border-zinc-800 text-xs text-zinc-600">
              Showing {filtered.length} of {matches.length} matches
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
