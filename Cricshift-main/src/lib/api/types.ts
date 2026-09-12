/**
 * API Types — Phase 5
 * TypeScript interfaces matching the FastAPI Pydantic schemas exactly.
 * Verified against backend/schemas.py.
 */

/* ═══════════════════════════════════════════════════════════════════ */
/* HEALTH                                                             */
/* ═══════════════════════════════════════════════════════════════════ */

export interface HealthResponse {
  status: string;
  service: string;
  models_loaded: boolean;
  model_status: Record<string, boolean>;
}

/* ═══════════════════════════════════════════════════════════════════ */
/* MATCH STATE (shared input for prediction endpoints)                */
/* ═══════════════════════════════════════════════════════════════════ */

export interface MatchStateRequest {
  batting_team: string;
  bowling_team: string;
  venue: string;
  innings: number;
  current_over: number;
  current_ball: number;
  current_score: number;
  current_wickets: number;
  target: number;
  batter_name: string;
  bowler_name: string;
  season: string;
  /* Rolling window features — defaults to 0 on backend if omitted */
  runs_last_6_balls: number;
  runs_last_12_balls: number;
  runs_last_18_balls: number;
  runs_last_30_balls: number;
  wickets_last_6_balls: number;
  wickets_last_12_balls: number;
  boundaries_last_6_balls: number;
  boundaries_last_12_balls: number;
  dot_balls_last_6_balls: number;
  dot_balls_last_12_balls: number;
}

/* ═══════════════════════════════════════════════════════════════════ */
/* WIN PREDICTION                                                     */
/* ═══════════════════════════════════════════════════════════════════ */

export interface WinProbabilityResponse {
  team_a: string;
  team_b: string;
  win_probability: Record<string, number>;
  predicted_winner: string;
  confidence: number;
}

/* ═══════════════════════════════════════════════════════════════════ */
/* MOMENTUM                                                           */
/* ═══════════════════════════════════════════════════════════════════ */

export interface MomentumResponse {
  momentum_class: string;
  probabilities: Record<string, number>;
  confidence: number;
}

/* ═══════════════════════════════════════════════════════════════════ */
/* COMBINED MATCH INTELLIGENCE                                        */
/* ═══════════════════════════════════════════════════════════════════ */

export interface MatchIntelligenceResponse {
  match_state: Record<string, unknown>;
  win_probability: Record<string, number>;
  predicted_winner: string;
  momentum: Record<string, unknown>;
  confidence: Record<string, number>;
  key_indicators: Record<string, unknown>;
}

/* ═══════════════════════════════════════════════════════════════════ */
/* RECOMMENDATION                                                     */
/* ═══════════════════════════════════════════════════════════════════ */

export interface RecommendationRequest {
  batting_team: string;
  bowling_team: string;
  venue: string;
  current_score: number;
  current_wickets: number;
  current_over: number;       // float on backend
  required_run_rate: number;
  pressure_index: number;
  momentum_score: number;
  current_batter: string;
  current_bowler: string;
  dismissed_batters: string[];
  top_n: number;
}

export interface PlayerRecommendation {
  Player: string;
  Recommendation_Score: number;
  Reason: string;
  Expected_Impact: number;
  Confidence: number;
}

export interface RecommendationResponse {
  batting_team: string;
  scenario: string;
  recommendations: PlayerRecommendation[];
}

/* ═══════════════════════════════════════════════════════════════════ */
/* EXPLAINABILITY                                                     */
/* ═══════════════════════════════════════════════════════════════════ */

export interface ExplainRequest {
  batting_team: string;
  bowling_team: string;
  venue: string;
  innings: number;
  current_over: number;
  current_ball: number;
  current_score: number;
  current_wickets: number;
  target: number;
  batter_name: string;
  bowler_name: string;
  season: string;
  model: "momentum" | "win" | "both";
}

export interface ExplainResponse {
  model_used: string;
  predictions: Record<string, unknown>;
  feature_contributions: Record<string, unknown>;
  top_features: string[];
}

/* ═══════════════════════════════════════════════════════════════════ */
/* SIMULATION                                                         */
/* ═══════════════════════════════════════════════════════════════════ */

export interface SimulationRequest {
  batting_team: string;
  bowling_team: string;
  venue: string;
  innings: number;
  current_over: number;
  current_ball: number;
  current_score: number;
  current_wickets: number;
  target: number;
  batter_name: string;
  bowler_name: string;
  season: string;
  modifications: Record<string, unknown>;
  scenario_name: string;
}

export interface SimulationResponse {
  scenario_name: string;
  modifications: Record<string, unknown>;
  original: Record<string, unknown>;
  modified: Record<string, unknown>;
  delta: Record<string, unknown>;
  explanation: string;
}

/* ═══════════════════════════════════════════════════════════════════ */
/* ANALYTICS                                                          */
/* ═══════════════════════════════════════════════════════════════════ */

export interface PlayerStatsResponse {
  total: number;
  players: Record<string, unknown>[];
}

export interface TeamStatsResponse {
  total: number;
  teams: Record<string, unknown>[];
}

export interface VenueStatsResponse {
  total: number;
  venues: Record<string, unknown>[];
}

/* ═══════════════════════════════════════════════════════════════════ */
/* MONTE CARLO SIMULATION                                             */
/* ═══════════════════════════════════════════════════════════════════ */

export interface MonteCarloRequest {
  current_score: number;
  current_wickets: number;
  current_over: number;
  current_ball?: number;
  target?: number;
  total_overs?: number;
  num_simulations?: number;
  batter_name?: string;
  bowler_name?: string;
}

export interface ScoreDistributionBin {
  range: string;
  min: number;
  max: number;
  count: number;
  probability: number;
}

export interface MonteCarloResponse {
  simulations_run: number;
  target?: number;
  win_probability_pct: number;
  median_score: number;
  mean_score: number;
  std_score: number;
  min_score: number;
  max_score: number;
  percentiles: {
    p10: number;
    p25: number;
    p50: number;
    p75: number;
    p90: number;
  };
  expected_wickets_lost: number;
  expected_wickets_remaining: number;
  most_likely_score_range: string;
  score_distribution: ScoreDistributionBin[];
}

/* ═══════════════════════════════════════════════════════════════════ */
/* AI COMMENTARY                                                      */
/* ═══════════════════════════════════════════════════════════════════ */

export interface CommentaryRequest {
  batting_team: string;
  bowling_team: string;
  current_over: number;
  current_ball?: number;
  current_score: number;
  current_wickets: number;
  target?: number;
  win_prob_batting?: number;
  win_prob_delta?: number;
  momentum_label?: string;
  batter_name?: string;
  bowler_name?: string;
  top_shap_features?: string[];
}

export interface CommentaryResponse {
  headline: string;
  commentary: string;
  tactical_insight: string;
  primary_driver: string;
  tone: "CRITICAL" | "MOMENTUM_SHIFT" | "TACTICAL_PRESSURE" | "DOMINANT" | "BALANCED";
  impact_rating: number;
  win_probability_batting: number;
  momentum_label: string;
}

/* ═══════════════════════════════════════════════════════════════════ */
/* MATCHUP ANALYTICS                                                  */
/* ═══════════════════════════════════════════════════════════════════ */

export interface MatchupRecord {
  Batter: string;
  Bowler: string;
  Balls_Faced: number;
  Runs_Scored: number;
  Dismissals: number;
  Fours: number;
  Sixes: number;
  Dot_Balls: number;
  Strike_Rate: number;
  Dot_Percentage: number;
  Boundary_Percentage: number;
}

export interface MatchupResponse {
  found: boolean;
  batter: string;
  bowler: string;
  matchup?: MatchupRecord;
  message?: string;
}

export interface PlayerMatchupsResponse {
  player_type: "batter" | "bowler";
  player_name: string;
  count: number;
  matchups: MatchupRecord[];
}

export interface MatchupMatrixResponse {
  batters: string[];
  bowlers: string[];
  total_records: number;
  matrix: MatchupRecord[];
}

