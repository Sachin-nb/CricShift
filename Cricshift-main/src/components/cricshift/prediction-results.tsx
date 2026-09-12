"use client";

import { motion } from "framer-motion";
import {
  TrendingUp,
  Activity,
  Brain,
  Crown,
  Gauge,
  Users,
  Loader2,
  AlertCircle,
  Target,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type {
  MatchIntelligenceResponse,
  ExplainResponse,
  RecommendationResponse,
} from "@/lib/api/types";
import { useState } from "react";

interface PredictionResultsProps {
  intelligence?: MatchIntelligenceResponse;
  isLoading: boolean;
  error: Error | null;
  explainData?: ExplainResponse;
  explainLoading: boolean;
  onExplain: () => void;
  recommendData?: RecommendationResponse;
  recommendLoading: boolean;
  onRecommend: () => void;
}

export function PredictionResults({
  intelligence,
  isLoading,
  error,
  explainData,
  explainLoading,
  onExplain,
  recommendData,
  recommendLoading,
  onRecommend,
}: PredictionResultsProps) {
  const [showExplain, setShowExplain] = useState(false);
  const [showRecommend, setShowRecommend] = useState(false);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-400 mb-3" />
        <span className="text-sm">Analyzing match intelligence…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-6 text-center">
        <AlertCircle className="mx-auto h-8 w-8 text-red-400 mb-2" />
        <p className="text-sm text-red-300 font-medium">Prediction failed</p>
        <p className="text-xs text-muted-foreground mt-1">{error.message}</p>
      </div>
    );
  }

  if (!intelligence) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <Target className="h-12 w-12 text-muted-foreground/30 mb-4" />
        <p className="text-sm text-muted-foreground">
          Enter match state and click predict
        </p>
        <p className="text-xs text-muted-foreground/60 mt-1">
          Results will appear here
        </p>
      </div>
    );
  }

  const {
    win_probability,
    predicted_winner,
    momentum,
    confidence,
    key_indicators,
  } = intelligence;
  const teams = Object.keys(win_probability);
  const momRec = momentum as Record<string, unknown>;
  const momClass = String(momRec?.class ?? momRec?.momentum_class ?? "Unknown");
  const momProbs = (momRec?.probabilities ?? {}) as Record<string, number>;
  const momConfidence = Number(
    momRec?.confidence ??
      (Object.values(momProbs).length > 0
        ? Math.max(...Object.values(momProbs))
        : 0),
  );

  return (
    <div className="space-y-4">
      {/* ─── Win Probability ─────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/5 to-transparent p-5"
      >
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="h-4 w-4 text-emerald-400" />
          <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Win Probability
          </span>
        </div>
        {teams.map((team) => {
          const pct = win_probability[team] ?? 0;
          const isWinner = team === predicted_winner;
          return (
            <div key={team} className="mb-3 last:mb-0">
              <div className="flex items-center justify-between mb-1.5">
                <span
                  className={`text-sm font-medium ${isWinner ? "text-emerald-300" : "text-muted-foreground"}`}
                >
                  {team}{" "}
                  {isWinner && (
                    <Crown className="inline h-3.5 w-3.5 text-amber-400 ml-1" />
                  )}
                </span>
                <span
                  className={`font-mono text-sm font-bold ${isWinner ? "text-emerald-300" : "text-muted-foreground"}`}
                >
                  {pct.toFixed(1)}%
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
                <motion.div
                  className={`h-full rounded-full ${isWinner ? "bg-gradient-to-r from-emerald-400 to-emerald-500" : "bg-white/20"}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
                />
              </div>
            </div>
          );
        })}
        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-muted-foreground">
          <span>
            Predicted Winner:{" "}
            <span className="text-emerald-300 font-semibold">
              {predicted_winner}
            </span>
          </span>
          {Object.entries(confidence).map(([k, v]) => (
            <span key={k}>
              {k} confidence:{" "}
              <span className="font-mono text-emerald-300">
                {(Number(v) * 100).toFixed(1)}%
              </span>
            </span>
          ))}
        </div>
      </motion.div>

      {/* ─── Momentum ────────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="rounded-xl border border-white/10 bg-gradient-to-br from-white/[0.05] to-transparent p-5"
      >
        <div className="flex items-center gap-2 mb-3">
          <Activity className="h-4 w-4 text-amber-400" />
          <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            Momentum
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`rounded-lg px-3 py-1.5 text-sm font-bold ${
              momClass === "Positive"
                ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                : momClass === "Negative"
                  ? "bg-red-500/15 text-red-300 border border-red-500/30"
                  : "bg-amber-400/15 text-amber-300 border border-amber-400/30"
            }`}
          >
            {momClass}
          </span>
          <span className="text-xs text-muted-foreground">
            Confidence:{" "}
            <span className="font-mono text-white">
              {(momConfidence * 100).toFixed(1)}%
            </span>
          </span>
        </div>
        {Object.keys(momProbs).length > 0 && (
          <div className="mt-3 grid grid-cols-3 gap-2">
            {Object.entries(momProbs).map(([label, prob]) => (
              <div
                key={label}
                className="rounded-lg bg-white/[0.03] p-2 text-center"
              >
                <div className="text-[10px] uppercase tracking-widest text-muted-foreground">
                  {label}
                </div>
                <div className="font-mono text-sm font-bold text-white">
                  {(Number(prob) * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        )}
      </motion.div>

      {/* ─── Key Indicators ──────────────────────────────────────── */}
      {key_indicators && Object.keys(key_indicators).length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-xl border border-white/10 bg-white/[0.03] p-5"
        >
          <div className="flex items-center gap-2 mb-3">
            <Gauge className="h-4 w-4 text-emerald-400" />
            <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              Key Indicators
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {Object.entries(key_indicators).map(([key, val]) => (
              <div
                key={key}
                className="rounded-lg bg-white/[0.03] border border-white/5 p-2.5"
              >
                <div className="text-[10px] uppercase tracking-widest text-muted-foreground truncate">
                  {key.replace(/_/g, " ")}
                </div>
                <div className="font-mono text-sm font-semibold text-white mt-0.5">
                  {typeof val === "number" ? val.toFixed(2) : String(val)}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* ─── Explainability ──────────────────────────────────────── */}
      <div className="rounded-xl border border-white/10 bg-black/30 backdrop-blur-md overflow-hidden">
        <button
          onClick={() => {
            setShowExplain(!showExplain);
            if (!explainData && !explainLoading) onExplain();
          }}
          className="flex w-full items-center justify-between p-4 text-left hover:bg-white/[0.02] transition-colors"
        >
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4 text-emerald-400" />
            <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              Explainable AI
            </span>
          </div>
          {showExplain ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </button>
        {showExplain && (
          <div className="border-t border-white/5 p-4">
            {explainLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /> Generating
                explanation…
              </div>
            ) : explainData ? (
              <div className="space-y-3">
                <div>
                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">
                    Model: {explainData.model_used}
                  </div>
                </div>
                {explainData.top_features && explainData.top_features.length > 0 && (
                  <div>
                    <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">
                      Top Features
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {explainData.top_features.map((f: string, i: number) => (
                        <span
                          key={f}
                          className="rounded-full border border-emerald-500/20 bg-emerald-500/5 px-2.5 py-0.5 text-[11px] text-emerald-300"
                        >
                          #{i + 1} {f.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {explainData.feature_contributions &&
                  Object.keys(explainData.feature_contributions).length > 0 && (
                  <div>
                    <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-2">
                      Feature Contributions
                    </div>
                    {Object.entries(explainData.feature_contributions).map(
                      ([modelName, contributions]) => (
                        <div key={modelName} className="mb-3 last:mb-0">
                          <div className="text-[10px] uppercase tracking-widest text-emerald-400/70 mb-1.5">
                            {modelName}
                          </div>
                          <div className="space-y-1.5 max-h-48 overflow-y-auto no-scrollbar">
                            {(Array.isArray(contributions)
                              ? contributions
                              : Object.entries(contributions as Record<string, number>).map(
                                  ([k, v]) => ({ feature: k, importance: v }),
                                )
                            )
                              .slice(0, 10)
                              .map(
                                (item: { feature: string; importance: number; value?: number }) => (
                                  <div
                                    key={item.feature}
                                    className="flex items-center justify-between text-xs"
                                  >
                                    <span className="text-muted-foreground truncate mr-2">
                                      {item.feature.replace(/_/g, " ")}
                                    </span>
                                    <span className="font-mono text-emerald-300">
                                      {item.importance.toFixed(4)}
                                    </span>
                                  </div>
                                ),
                              )}
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">
                Click to generate explanation
              </p>
            )}
          </div>
        )}
      </div>

      {/* ─── Player Recommendation ───────────────────────────────── */}
      <div className="rounded-xl border border-white/10 bg-black/30 backdrop-blur-md overflow-hidden">
        <button
          onClick={() => {
            setShowRecommend(!showRecommend);
            if (!recommendData && !recommendLoading) onRecommend();
          }}
          className="flex w-full items-center justify-between p-4 text-left hover:bg-white/[0.02] transition-colors"
        >
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-amber-400" />
            <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              Player Recommendations
            </span>
          </div>
          {showRecommend ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </button>
        {showRecommend && (
          <div className="border-t border-white/5 p-4">
            {recommendLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /> Finding
                recommendations…
              </div>
            ) : recommendData ? (
              <div className="space-y-2">
                <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-2">
                  {recommendData.scenario}
                </div>
                {recommendData.recommendations.map((rec) => (
                  <div
                    key={rec.Player}
                    className="rounded-lg border border-white/10 bg-white/[0.03] p-3"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-semibold text-white">
                        {rec.Player}
                      </span>
                      <span className="font-mono text-sm font-bold text-emerald-300">
                        {rec.Recommendation_Score.toFixed(1)}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">
                      {rec.Reason}
                    </p>
                    <div className="flex gap-4 text-[11px]">
                      <span className="text-muted-foreground">
                        Impact:{" "}
                        <span className="text-amber-300 font-mono">
                          {rec.Expected_Impact.toFixed(2)}
                        </span>
                      </span>
                      <span className="text-muted-foreground">
                        Confidence:{" "}
                        <span className="text-emerald-300 font-mono">
                          {(rec.Confidence * 100).toFixed(0)}%
                        </span>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">
                Click to get player recommendations
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
