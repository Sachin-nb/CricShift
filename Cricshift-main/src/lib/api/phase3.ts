import { useQuery, useMutation } from "@tanstack/react-query";
import { apiGet, apiPost } from "./client";

export function usePlayers(search?: string, minMatches = 0) {
  return useQuery({
    queryKey: ["players", search, minMatches],
    queryFn: () => apiGet<any>("/api/analytics/players", { search, min_matches: minMatches }),
  });
}

export function useRecommendPlayer() {
  return useMutation({
    mutationFn: (situation: any) => apiPost<any>("/api/recommend/player", situation),
  });
}

export function useSimulate() {
  return useMutation({
    mutationFn: (request: any) => apiPost<any>("/api/simulate", request),
  });
}

export function useExplain() {
  return useMutation({
    mutationFn: (request: any) => apiPost<any>("/api/explain", request),
  });
}
