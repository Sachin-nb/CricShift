import { useMutation } from "@tanstack/react-query";
import { apiPostForm } from "./client";

export interface HistoricalTimelinePoint {
  over: number;
  innings: number;
  score: number;
  wickets: number;
  momentum_class: string;
  momentum_probabilities: Record<string, number>;
  win_probability: Record<string, number>;
  batter: string;
  bowler: string;
}

export interface HistoricalTurningPoint {
  over: number;
  innings: number;
  description: string;
  win_prob: Record<string, number>;
}

export interface HistoricalAnalysisResponse {
  analysis_id: string;
  match_info: {
    match_id: string;
    batting_team: string;
    bowling_team: string;
    venue: string;
  };
  timeline: HistoricalTimelinePoint[];
  turning_points: HistoricalTurningPoint[];
  latest_state: any;
}

export function useUploadHistoricalDataset() {
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return apiPostForm<HistoricalAnalysisResponse>("/api/historical/upload", formData);
    },
  });
}
