/**
 * Admin API hooks — all data comes from /api/admin/* on the FastAPI backend.
 * Re-fetches every 30 s so the dashboard stays current without a page reload.
 */
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "./client";

// ─────────────────────────────────────────────────────────────────────────────
// Types mirroring the Python activity_db tables
// ─────────────────────────────────────────────────────────────────────────────

export interface AdminStats {
  total_live_matches: number;
  total_predictions: number;
  total_simulations: number;
  total_historical: number;
  live_matches_today: number;
  predictions_today: number;
  simulations_today: number;
  historical_today: number;
}

export interface LiveMatchRecord {
  id: number;
  match_id: string;
  team_a: string;
  team_b: string;
  series: string;
  venue: string;
  match_format: string;
  status: string;
  first_seen_at: string;
  last_seen_at: string;
  fetch_count: number;
}

export interface PredictionRecord {
  id: number;
  type: "win" | "momentum" | "match";
  batting_team: string;
  bowling_team: string;
  venue: string;
  innings: number;
  current_over: number;
  current_score: number;
  current_wickets: number;
  target: number;
  predicted_winner: string;
  win_prob_batting: number;
  momentum_class: string;
  confidence: number;
  created_at: string;
}

export interface SimulationRecord {
  id: number;
  scenario_name: string;
  batting_team: string;
  bowling_team: string;
  venue: string;
  innings: number;
  current_over: number;
  current_score: number;
  current_wickets: number;
  target: number;
  modifications_json: string;
  original_win_prob: number;
  modified_win_prob: number;
  original_momentum: string;
  modified_momentum: string;
  delta_json: string;
  explanation: string;
  created_at: string;
}

export interface HistoricalAnalysisRecord {
  id: number;
  analysis_id: string;
  filename: string;
  match_id: string;
  batting_team: string;
  bowling_team: string;
  venue: string;
  timeline_length: number;
  turning_points_count: number;
  file_size_kb: number;
  created_at: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Hooks
// ─────────────────────────────────────────────────────────────────────────────

const POLL = 30_000; // 30 s

export function useAdminStats() {
  return useQuery<AdminStats>({
    queryKey: ["adminStats"],
    queryFn: () => apiGet<AdminStats>("/api/admin/stats"),
    refetchInterval: POLL,
    retry: 1,
  });
}

export function useAdminMatches(limit = 100, offset = 0) {
  return useQuery<LiveMatchRecord[]>({
    queryKey: ["adminMatches", limit, offset],
    queryFn: () =>
      apiGet<LiveMatchRecord[]>("/api/admin/matches", { limit, offset }),
    refetchInterval: POLL,
    retry: 1,
  });
}

export function useAdminPredictions(limit = 100, offset = 0) {
  return useQuery<PredictionRecord[]>({
    queryKey: ["adminPredictions", limit, offset],
    queryFn: () =>
      apiGet<PredictionRecord[]>("/api/admin/predictions", { limit, offset }),
    refetchInterval: POLL,
    retry: 1,
  });
}

export function useAdminSimulations(limit = 100, offset = 0) {
  return useQuery<SimulationRecord[]>({
    queryKey: ["adminSimulations", limit, offset],
    queryFn: () =>
      apiGet<SimulationRecord[]>("/api/admin/simulations", { limit, offset }),
    refetchInterval: POLL,
    retry: 1,
  });
}

export function useAdminHistorical(limit = 100, offset = 0) {
  return useQuery<HistoricalAnalysisRecord[]>({
    queryKey: ["adminHistorical", limit, offset],
    queryFn: () =>
      apiGet<HistoricalAnalysisRecord[]>("/api/admin/historical", {
        limit,
        offset,
      }),
    refetchInterval: POLL,
    retry: 1,
  });
}

export function useAdminHistoricalDetail(analysisId: string) {
  return useQuery<Record<string, any>>({
    queryKey: ["adminHistoricalDetail", analysisId],
    queryFn: () =>
      apiGet<Record<string, any>>(`/api/admin/historical/${analysisId}`),
    enabled: !!analysisId,
    retry: 1,
  });
}
