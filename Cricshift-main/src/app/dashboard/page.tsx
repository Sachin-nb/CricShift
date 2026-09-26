"use client";

import { useRef } from "react";
import { PageShell } from "@/components/cricshift/page-shell";
import { Card } from "@/components/cricshift/card";
import { MatchStateForm } from "@/components/cricshift/match-state-form";
import { PredictionResults } from "@/components/cricshift/prediction-results";
import { ApiStatus } from "@/components/cricshift/api-status";
import {
  useMatchIntelligence,
  useExplainability,
  usePlayerRecommendation,
} from "@/lib/api/hooks";
import type { MatchStateFormData } from "@/lib/api/validation";
import type { ExplainRequest, RecommendationRequest } from "@/lib/api/types";
import { Activity } from "lucide-react";

export default function DashboardPage() {
  const intelligence = useMatchIntelligence();
  const explain = useExplainability();
  const recommend = usePlayerRecommendation();
  const lastFormData = useRef<MatchStateFormData | null>(null);

  function handleSubmit(data: MatchStateFormData) {
    lastFormData.current = data;
    explain.reset();
    recommend.reset();
    intelligence.mutate(data);
  }

  function handleExplain() {
    const d = lastFormData.current;
    if (!d) return;
    const req: ExplainRequest = {
      batting_team: d.batting_team,
      bowling_team: d.bowling_team,
      venue: d.venue,
      innings: d.innings,
      current_over: d.current_over,
      current_ball: d.current_ball,
      current_score: d.current_score,
      current_wickets: d.current_wickets,
      target: d.target,
      batter_name: d.batter_name,
      bowler_name: d.bowler_name,
      season: d.season,
      model: "both",
    };
    explain.mutate(req);
  }

  function handleRecommend() {
    const d = lastFormData.current;
    if (!d) return;
    const ballsBowled = d.current_over * 6 + d.current_ball;
    const ballsRemaining = Math.max(1, 120 - ballsBowled);
    const rrr =
      d.target > 0
        ? ((d.target - d.current_score) / ballsRemaining) * 6
        : 0;
    const pressureIndex = rrr + d.current_wickets * 2;

    const momRec = intelligence.data?.momentum as Record<string, unknown> | undefined;
    const momClass = String(
      momRec?.class ?? momRec?.momentum_class ?? "Neutral",
    );
    const momentumScore =
      momClass === "Positive" ? 1 : momClass === "Negative" ? -1 : 0;

    const req: RecommendationRequest = {
      batting_team: d.batting_team,
      bowling_team: d.bowling_team,
      venue: d.venue,
      current_score: d.current_score,
      current_wickets: d.current_wickets,
      current_over: d.current_over + d.current_ball / 10,
      required_run_rate: Math.round(rrr * 100) / 100,
      pressure_index: Math.round(pressureIndex * 100) / 100,
      momentum_score: momentumScore,
      current_batter: d.batter_name,
      current_bowler: d.bowler_name,
      dismissed_batters: [],
      top_n: 5,
    };
    recommend.mutate(req);
  }

  return (
    <PageShell
      eyebrow="Match Intelligence"
      eyebrowIcon={Activity}
      title="Match"
      titleAccent="Intelligence"
      subtitle="Enter the match state for live AI-powered predictions."
      actions={<ApiStatus />}
    >
      {/* Two-column layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* Left: Form */}
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center gap-2 mb-5">
              <Activity className="h-4 w-4 text-emerald-400" />
              <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                Match State
              </span>
            </div>
            <MatchStateForm
              onSubmit={handleSubmit}
              isLoading={intelligence.isPending}
            />
          </Card>
        </div>

        {/* Right: Results */}
        <div className="lg:col-span-3">
          <PredictionResults
            intelligence={intelligence.data}
            isLoading={intelligence.isPending}
            error={intelligence.error}
            explainData={explain.data}
            explainLoading={explain.isPending}
            onExplain={handleExplain}
            recommendData={recommend.data}
            recommendLoading={recommend.isPending}
            onRecommend={handleRecommend}
          />
        </div>
      </div>
    </PageShell>
  );
}
