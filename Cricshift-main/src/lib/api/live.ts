import { useQuery, useMutation } from "@tanstack/react-query";
import { apiGet } from "./client";

export interface LiveMatch {
  match_id: number | string;
  series: string;
  status: string;
  match_format: string;
  team_a: string;
  team_a_score: string;
  team_a_overs: string;
  team_b: string;
  team_b_score: string;
  team_b_overs: string;
  venue: string;
}

export function useLiveMatches() {
  return useQuery({
    queryKey: ["liveMatches"],
    queryFn: () => apiGet<LiveMatch[]>("/api/live/matches", undefined, 8_000),
    refetchInterval: 15_000, // Poll every 15s
    retry: 2,
  });
}

export function useLiveMatch(matchId: string) {
  return useQuery({
    queryKey: ["liveMatch", matchId],
    // Short timeout: /match just normalizes the scorecard, should be fast
    queryFn: () => apiGet<any>(`/api/live/match/${matchId}`, undefined, 8_000),
    refetchInterval: 15_000,
    enabled: !!matchId,
  });
}

export function useLiveMatchIntelligence(matchId: string) {
  return useQuery({
    queryKey: ["liveMatchIntelligence", matchId],
    // Intelligence runs batch ML prediction over every ball — allow full 30s
    queryFn: () => apiGet<any>(`/api/live/match/${matchId}/intelligence`, undefined, 30_000),
    refetchInterval: 30_000, // Poll less often since it's expensive
    enabled: !!matchId,
    retry: 1,
  });
}

import { useEffect, useState } from "react";

export function useLiveWebSocket(matchId: string) {
  const [data, setData] = useState<any>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!matchId) return;

    const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
    const wsUrl = apiBase.replace(/^http/, "ws") + `/ws/live/${matchId}`;

    let ws: WebSocket | null = null;
    let reconnectTimer: NodeJS.Timeout | null = null;
    let isSubscribed = true;

    function connect() {
      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          if (isSubscribed) {
            setIsConnected(true);
            setError(null);
          }
        };

        ws.onmessage = (event) => {
          if (!isSubscribed) return;
          try {
            const payload = JSON.parse(event.data);
            if (payload.data) {
              setData(payload.data);
            }
          } catch (e) {
            // Ignore parse errors
          }
        };

        ws.onerror = () => {
          if (isSubscribed) {
            setError("WebSocket stream interrupted");
          }
        };

        ws.onclose = () => {
          if (isSubscribed) {
            setIsConnected(false);
            reconnectTimer = setTimeout(connect, 5000);
          }
        };
      } catch (err: any) {
        if (isSubscribed) {
          setError(err?.message ?? "WebSocket connection error");
        }
      }
    }

    connect();

    return () => {
      isSubscribed = false;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) ws.close();
    };
  }, [matchId]);

  return { data, isConnected, error };
}

