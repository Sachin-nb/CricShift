/**
 * React Query Hooks — Phase 5
 * TanStack React Query wrappers for every FastAPI endpoint.
 */

import { useQuery, useMutation } from "@tanstack/react-query";
import { apiGet, apiPost } from "./client";
import type {
  HealthResponse,
  PlayerStatsResponse,
  TeamStatsResponse,
  VenueStatsResponse,
  MatchStateRequest,
  WinProbabilityResponse,
  MomentumResponse,
  MatchIntelligenceResponse,
  RecommendationRequest,
  RecommendationResponse,
  ExplainRequest,
  ExplainResponse,
  SimulationRequest,
  SimulationResponse,
  MonteCarloRequest,
  MonteCarloResponse,
  CommentaryRequest,
  CommentaryResponse,
  MatchupResponse,
  PlayerMatchupsResponse,
  MatchupMatrixResponse,
} from "./types";

/* ═══════════════════════════════════════════════════════════════════ */
/* QUERIES (GET)                                                      */
/* ═══════════════════════════════════════════════════════════════════ */

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => apiGet<HealthResponse>("/api/health"),
    refetchInterval: 30_000,
    retry: 1,
  });
}

export function usePlayers(
  params: {
    search?: string;
    min_matches?: number;
    limit?: number;
    offset?: number;
  } = {},
) {
  return useQuery({
    queryKey: ["players", params],
    queryFn: () =>
      apiGet<PlayerStatsResponse>("/api/analytics/players", {
        search: params.search,
        min_matches: params.min_matches,
        limit: params.limit ?? 50,
        offset: params.offset ?? 0,
      }),
    staleTime: 5 * 60_000,
  });
}

export function useTeams(search?: string) {
  return useQuery({
    queryKey: ["teams", search],
    queryFn: () =>
      apiGet<TeamStatsResponse>("/api/analytics/teams", { search }),
    staleTime: 5 * 60_000,
  });
}

export function useVenues(search?: string) {
  return useQuery({
    queryKey: ["venues", search],
    queryFn: () =>
      apiGet<VenueStatsResponse>("/api/analytics/venues", { search }),
    staleTime: 5 * 60_000,
  });
}

/* ═══════════════════════════════════════════════════════════════════ */
/* MUTATIONS (POST)                                                   */
/* ═══════════════════════════════════════════════════════════════════ */

export function useWinPrediction() {
  return useMutation({
    mutationFn: (data: MatchStateRequest) =>
      apiPost<WinProbabilityResponse>("/api/predict/win", data),
  });
}

export function useMomentumPrediction() {
  return useMutation({
    mutationFn: (data: MatchStateRequest) =>
      apiPost<MomentumResponse>("/api/predict/momentum", data),
  });
}

export function useMatchIntelligence() {
  return useMutation({
    mutationFn: (data: MatchStateRequest) =>
      apiPost<MatchIntelligenceResponse>("/api/predict/match", data),
  });
}

export function usePlayerRecommendation() {
  return useMutation({
    mutationFn: (data: RecommendationRequest) =>
      apiPost<RecommendationResponse>("/api/recommend/player", data),
  });
}

export function useExplainability() {
  return useMutation({
    mutationFn: (data: ExplainRequest) =>
      apiPost<ExplainResponse>("/api/explain", data),
  });
}

export function useSimulation() {
  return useMutation({
    mutationFn: (data: SimulationRequest) =>
      apiPost<SimulationResponse>("/api/simulate", data),
  });
}

export function useMonteCarloSimulation() {
  return useMutation({
    mutationFn: (data: MonteCarloRequest) =>
      apiPost<MonteCarloResponse>("/api/simulate/monte-carlo", data),
  });
}

export function useAICommentary() {
  return useMutation({
    mutationFn: (data: CommentaryRequest) =>
      apiPost<CommentaryResponse>("/api/commentary/generate", data),
  });
}

export function useMatchup(batter?: string, bowler?: string) {
  return useQuery({
    queryKey: ["matchup", batter, bowler],
    queryFn: () =>
      apiGet<MatchupResponse>("/api/analytics/matchup", {
        batter,
        bowler,
      }),
    enabled: Boolean(batter && bowler),
    staleTime: 5 * 60_000,
  });
}

export function usePlayerMatchups(
  params: {
    batter?: string;
    bowler?: string;
    min_balls?: number;
    limit?: number;
  } = {}
) {
  return useQuery({
    queryKey: ["playerMatchups", params],
    queryFn: () =>
      apiGet<PlayerMatchupsResponse>("/api/analytics/matchups", {
        batter: params.batter,
        bowler: params.bowler,
        min_balls: params.min_balls ?? 1,
        limit: params.limit ?? 25,
      }),
    enabled: Boolean(params.batter || params.bowler),
    staleTime: 5 * 60_000,
  });
}

export function useMatchupMatrix(batters: string[], bowlers: string[]) {
  return useQuery({
    queryKey: ["matchupMatrix", batters, bowlers],
    queryFn: () =>
      apiGet<MatchupMatrixResponse>("/api/analytics/matchups/matrix", {
        batters: batters.join(","),
        bowlers: bowlers.join(","),
      }),
    enabled: Boolean(batters.length > 0 && bowlers.length > 0),
    staleTime: 5 * 60_000,
  });
}

