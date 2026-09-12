"""
Pydantic Schemas — Phase 4
Request and response models for all API endpoints.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ═════════════════════════════════════════════════════════════════════
# HEALTH
# ═════════════════════════════════════════════════════════════════════

class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "cricket-analytics-api"
    models_loaded: bool
    model_status: Dict[str, bool] = {}


# ═════════════════════════════════════════════════════════════════════
# MATCH STATE (shared input — all prediction endpoints inherit from this)
# ═════════════════════════════════════════════════════════════════════

class MatchStateRequest(BaseModel):
    """Common match-state input accepted by prediction endpoints."""
    batting_team: str = Field(..., min_length=1, description="Name of the batting team")
    bowling_team: str = Field(..., min_length=1, description="Name of the bowling team")
    venue: str = Field("Unknown", description="Match venue")
    innings: int = Field(1, ge=1, le=2, description="Innings number (1 or 2)")
    current_over: int = Field(..., ge=0, le=20, description="Current over (0–20)")
    current_ball: int = Field(0, ge=0, le=6, description="Ball within the over (0–6)")
    current_score: int = Field(..., ge=0, description="Current runs scored")
    current_wickets: int = Field(..., ge=0, le=10, description="Wickets fallen")
    target: int = Field(0, ge=0, description="Target score (2nd innings only)")
    batter_name: str = Field("Unknown", description="Current batter's name")
    bowler_name: str = Field("Unknown", description="Current bowler's name")
    season: str = Field("2024", description="IPL season / year")

    # Optional rolling features (defaults are reasonable zero-state)
    runs_last_6_balls: int = Field(0, ge=0)
    runs_last_12_balls: int = Field(0, ge=0)
    runs_last_18_balls: int = Field(0, ge=0)
    runs_last_30_balls: int = Field(0, ge=0)
    wickets_last_6_balls: int = Field(0, ge=0, le=10)
    wickets_last_12_balls: int = Field(0, ge=0, le=10)
    boundaries_last_6_balls: int = Field(0, ge=0)
    boundaries_last_12_balls: int = Field(0, ge=0)
    dot_balls_last_6_balls: int = Field(0, ge=0, le=6)
    dot_balls_last_12_balls: int = Field(0, ge=0, le=12)

    @field_validator("current_wickets")
    @classmethod
    def wickets_not_impossible(cls, v: int, info) -> int:
        """Wickets cannot exceed 10 and cannot be negative (already enforced by ge/le,
        but also sanity-check against current_ball if provided)."""
        if v > 10:
            raise ValueError("Wickets cannot exceed 10")
        return v

    @field_validator("target")
    @classmethod
    def target_required_for_innings2(cls, v: int, info) -> int:
        innings = info.data.get("innings", 1)
        if innings == 2 and v <= 0:
            raise ValueError("Target must be > 0 for 2nd innings")
        return v

    @model_validator(mode="after")
    def score_cannot_exceed_target(self) -> "MatchStateRequest":
        """In a second innings, the batting team cannot have already exceeded the target
        and still be in the middle of a live over (that would mean the match is over)."""
        if (
            self.innings == 2
            and self.target > 0
            and self.current_score > self.target
            and self.current_ball > 0
        ):
            raise ValueError(
                "current_score exceeds target mid-over — match should already be finished"
            )
        return self


# ═════════════════════════════════════════════════════════════════════
# WIN PREDICTION
# ═════════════════════════════════════════════════════════════════════

class WinProbabilityResponse(BaseModel):
    team_a: str
    team_b: str
    win_probability: Dict[str, float]
    predicted_winner: str
    confidence: float


# ═════════════════════════════════════════════════════════════════════
# MOMENTUM
# ═════════════════════════════════════════════════════════════════════

class MomentumResponse(BaseModel):
    momentum_class: str
    probabilities: Dict[str, float]
    confidence: float


# ═════════════════════════════════════════════════════════════════════
# COMBINED MATCH INTELLIGENCE
# ═════════════════════════════════════════════════════════════════════

class MatchIntelligenceResponse(BaseModel):
    match_state: Dict[str, Any]
    win_probability: Dict[str, float]
    predicted_winner: str
    momentum: Dict[str, Any]
    confidence: Dict[str, float]
    key_indicators: Dict[str, Any]


# ═════════════════════════════════════════════════════════════════════
# RECOMMENDATION
# ═════════════════════════════════════════════════════════════════════

class RecommendationRequest(BaseModel):
    batting_team: str = Field(..., min_length=1)
    bowling_team: str = Field(..., min_length=1)
    venue: str = Field("Unknown")
    current_score: int = Field(0, ge=0)
    current_wickets: int = Field(0, ge=0, le=10)
    current_over: float = Field(0, ge=0, le=20)
    required_run_rate: float = Field(0, ge=0)
    pressure_index: float = Field(0)
    momentum_score: float = Field(0)
    current_batter: str = Field("")
    current_bowler: str = Field("")
    dismissed_batters: List[str] = Field(default_factory=list)
    top_n: int = Field(5, ge=1, le=20)


class PlayerRecommendation(BaseModel):
    Player: str
    Recommendation_Score: float
    Reason: str
    Expected_Impact: float
    Confidence: float


class RecommendationResponse(BaseModel):
    batting_team: str
    scenario: str
    recommendations: List[PlayerRecommendation]


# ═════════════════════════════════════════════════════════════════════
# EXPLAINABILITY
# Inherits all match-state fields from MatchStateRequest and adds `model`.
# ═════════════════════════════════════════════════════════════════════

class ExplainRequest(MatchStateRequest):
    """Request body — accepts all match-state fields plus which model to explain."""
    model: Literal["momentum", "win", "both"] = Field(
        "both",
        description="Which model to explain: 'momentum', 'win', or 'both'",
    )


class ExplainResponse(BaseModel):
    model_used: str
    predictions: Dict[str, Any]
    feature_contributions: Dict[str, Any]
    top_features: List[str]


class CommentaryRequest(BaseModel):
    """Request body for AI-generated broadcast commentary."""
    batting_team: str
    bowling_team: str
    current_over: int = Field(..., ge=0, le=50)
    current_ball: int = Field(0, ge=0, le=6)
    current_score: int = Field(..., ge=0)
    current_wickets: int = Field(..., ge=0, le=10)
    target: Optional[int] = Field(None, ge=1)
    win_prob_batting: float = Field(50.0, ge=0.0, le=100.0)
    win_prob_delta: float = Field(0.0)
    momentum_label: str = Field("Neutral")
    batter_name: Optional[str] = None
    bowler_name: Optional[str] = None
    top_shap_features: Optional[List[str]] = None


class CommentaryResponse(BaseModel):
    headline: str
    commentary: str
    tactical_insight: str
    primary_driver: str
    tone: str
    impact_rating: int
    win_probability_batting: float
    momentum_label: str



# ═════════════════════════════════════════════════════════════════════
# SIMULATION
# Inherits all match-state fields from MatchStateRequest and adds what-if fields.
# ═════════════════════════════════════════════════════════════════════

class SimulationRequest(MatchStateRequest):
    """Request body for what-if simulation."""
    modifications: Dict[str, Any] = Field(
        ...,
        description="Dict of changes, e.g. {'replace_batter': 'V Kohli', 'Current_Score': 100}",
    )
    scenario_name: str = Field("Custom Scenario")


class SimulationResponse(BaseModel):
    scenario_name: str
    modifications: Dict[str, Any]
    original: Dict[str, Any]
    modified: Dict[str, Any]
    delta: Dict[str, Any]
    explanation: str


class MonteCarloRequest(BaseModel):
    """Request body for Monte Carlo stochastic match simulation."""
    current_score: int = Field(..., ge=0, description="Current runs scored")
    current_wickets: int = Field(..., ge=0, le=10, description="Current wickets lost")
    current_over: int = Field(..., ge=0, le=50, description="Current over (0-indexed or cricket over)")
    current_ball: int = Field(0, ge=0, le=6, description="Current ball in over (0-6)")
    target: Optional[int] = Field(None, ge=1, description="Target score if chasing in 2nd innings")
    total_overs: int = Field(20, ge=5, le=50, description="Total overs per innings (default 20 for T20)")
    num_simulations: int = Field(1000, ge=100, le=5000, description="Number of simulation iterations")
    batter_name: Optional[str] = Field(None, description="Current striker name")
    bowler_name: Optional[str] = Field(None, description="Current bowler name")


class MonteCarloResponse(BaseModel):
    simulations_run: int
    target: Optional[int]
    win_probability_pct: float
    median_score: float
    mean_score: float
    std_score: float
    min_score: int
    max_score: int
    percentiles: Dict[str, float]
    expected_wickets_lost: float
    expected_wickets_remaining: float
    most_likely_score_range: str
    score_distribution: List[Dict[str, Any]]



# ═════════════════════════════════════════════════════════════════════
# ANALYTICS
# ═════════════════════════════════════════════════════════════════════

class PlayerStatsResponse(BaseModel):
    total: int
    players: List[Dict[str, Any]]


class TeamStatsResponse(BaseModel):
    total: int
    teams: List[Dict[str, Any]]


class VenueStatsResponse(BaseModel):
    total: int
    venues: List[Dict[str, Any]]


# ═════════════════════════════════════════════════════════════════════
# ERROR
# ═════════════════════════════════════════════════════════════════════

class ErrorResponse(BaseModel):
    error: str
    detail: str = ""
    status_code: int = 422
