"""
Dependencies — Phase 4
Application-level dependency injection for FastAPI.
Loads all ML models and data at startup and provides them to routes.
"""

import pickle
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from backend.config import (
    MOMENTUM_MODEL_DIR, WIN_PREDICTION_MODEL_DIR,
    PLAYER_STATS_PATH, TEAM_STATS_PATH, VENUE_STATS_PATH,
    EXPLAINABILITY_DIR, MOMENTUM_LABELS, PROJECT_ROOT, DEFAULT_SEASON,
)

logger = logging.getLogger("backend")

# ── Ensure project root on path for existing module imports ──────────
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ═════════════════════════════════════════════════════════════════════
class ModelStore:
    """
    Singleton-like store that holds all loaded models and reference data.
    Populated once at application startup via ``load_all()``.
    """

    def __init__(self):
        # Momentum
        self.momentum_model = None
        self.momentum_features: list = []
        self.momentum_encoders: dict = {}
        self.momentum_loaded: bool = False

        # Win prediction
        self.win_model = None
        self.win_features: list = []
        self.win_encoders: dict = {}
        self.win_loaded: bool = False

        # Recommendation engine
        self.recommendation_engine = None
        self.recommendation_loaded: bool = False

        # Simulation engine
        self.simulation_engine = None
        self.simulation_loaded: bool = False

        # Monte Carlo Simulator
        self.monte_carlo_simulator = None
        self.monte_carlo_loaded: bool = False

        # Reference data
        self.player_stats: Optional[pd.DataFrame] = None
        self.team_stats: Optional[pd.DataFrame] = None
        self.venue_stats: Optional[pd.DataFrame] = None
        self.data_loaded: bool = False

        # Pre-loaded global feature importance table (avoids per-request CSV reads)
        self.global_feature_importance: Optional[pd.DataFrame] = None

        # Stores the exact error message for each component that failed to load.
        # Surfaced by GET /api/health so you can diagnose startup failures.
        self.load_errors: Dict[str, str] = {}

    # ── Load helpers ─────────────────────────────────────────────────
    def _load_model_assets(self, model_dir: Path):
        """Load model, feature columns, and label encoders from a directory.
        Errors include the specific asset name so failures are easier to diagnose."""
        try:
            with open(model_dir / "best_model.pkl", "rb") as f:
                model = pickle.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"best_model.pkl not found in {model_dir}")

        try:
            with open(model_dir / "feature_columns.pkl", "rb") as f:
                feature_cols = pickle.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"feature_columns.pkl not found in {model_dir}")

        try:
            with open(model_dir / "label_encoder.pkl", "rb") as f:
                encoders = pickle.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"label_encoder.pkl not found in {model_dir}")

        return model, feature_cols, encoders

    def load_all(self) -> Dict[str, bool]:
        """Load every model and dataset. Returns a status dict keyed by component name."""
        status: Dict[str, bool] = {}
        self.load_errors = {}

        # Momentum model
        try:
            self.momentum_model, self.momentum_features, self.momentum_encoders = (
                self._load_model_assets(MOMENTUM_MODEL_DIR)
            )
            self.momentum_loaded = True
            logger.info(f"✓ Momentum model loaded ({len(self.momentum_features)} features)")
        except Exception as e:
            self.load_errors["momentum"] = str(e)
            logger.error(f"✗ Momentum model failed: {e}")
        status["momentum"] = self.momentum_loaded

        # Win prediction model
        try:
            self.win_model, self.win_features, self.win_encoders = (
                self._load_model_assets(WIN_PREDICTION_MODEL_DIR)
            )
            self.win_loaded = True
            logger.info(f"✓ Win model loaded ({len(self.win_features)} features)")
        except Exception as e:
            self.load_errors["win_prediction"] = str(e)
            logger.error(f"✗ Win model failed: {e}")
        status["win_prediction"] = self.win_loaded

        # Recommendation engine
        try:
            from models.recommendation.recommendation_engine import RecommendationEngine
            self.recommendation_engine = RecommendationEngine()
            self.recommendation_engine.load_data()
            self.recommendation_loaded = True
            logger.info("✓ Recommendation engine loaded")
        except Exception as e:
            self.load_errors["recommendation"] = str(e)
            logger.error(f"✗ Recommendation engine failed: {e}")
        status["recommendation"] = self.recommendation_loaded

        # Simulation engine
        try:
            from models.simulation.simulation_engine import SimulationEngine
            self.simulation_engine = SimulationEngine()
            self.simulation_engine.load()
            self.simulation_loaded = True
            logger.info("✓ Simulation engine loaded")
        except Exception as e:
            self.load_errors["simulation"] = str(e)
            logger.error(f"✗ Simulation engine failed: {e}")
        status["simulation"] = self.simulation_loaded

        # Monte Carlo Simulator
        try:
            from models.simulation.monte_carlo import MonteCarloSimulator
            self.monte_carlo_simulator = MonteCarloSimulator(player_stats_df=self.player_stats)
            self.monte_carlo_loaded = True
            logger.info("✓ Monte Carlo simulator loaded")
        except Exception as e:
            self.load_errors["monte_carlo"] = str(e)
            logger.error(f"✗ Monte Carlo simulator failed: {e}")
        status["monte_carlo"] = self.monte_carlo_loaded

        # Reference data
        try:
            self.player_stats = pd.read_csv(PLAYER_STATS_PATH)
            self.team_stats = pd.read_csv(TEAM_STATS_PATH)
            self.venue_stats = pd.read_csv(VENUE_STATS_PATH)
            self.data_loaded = True
            logger.info(
                f"✓ Reference data loaded ({len(self.player_stats)} players, "
                f"{len(self.team_stats)} teams, {len(self.venue_stats)} venues)"
            )
        except Exception as e:
            self.load_errors["reference_data"] = str(e)
            logger.error(f"✗ Reference data failed: {e}")
        status["reference_data"] = self.data_loaded

        # Global feature importance (pre-load once — avoids per-request CSV reads in explainability)
        try:
            imp_path = EXPLAINABILITY_DIR / "global_feature_importance.csv"
            self.global_feature_importance = pd.read_csv(imp_path)
            logger.info("✓ Global feature importance loaded")
        except Exception as e:
            logger.warning(f"  Global feature importance not available: {e}")
            self.global_feature_importance = pd.DataFrame()

        return status

    @property
    def all_loaded(self) -> bool:
        return (
            self.momentum_loaded and self.win_loaded
            and self.recommendation_loaded and self.simulation_loaded
            and self.data_loaded
        )

    # ── Prediction helpers ───────────────────────────────────────────
    def build_feature_row(self, data: dict) -> pd.DataFrame:
        """Build a single-row DataFrame from API input matching the feature dataset schema."""
        balls_bowled = data.get("current_over", 0) * 6 + data.get("current_ball", 0)
        balls_remaining = max(0, 120 - balls_bowled)
        overs_remaining = balls_remaining / 6
        current_score = data.get("current_score", 0)
        target = data.get("target", 0)
        crr = (current_score / balls_bowled * 6) if balls_bowled > 0 else 0.0

        runs_remaining = max(0, target - current_score) if target > 0 else 0
        rrr = (runs_remaining / balls_remaining * 6) if balls_remaining > 0 and target > 0 else 0.0

        over = data.get("current_over", 0)

        # Rolling window values passed in from the request
        runs_last_6   = data.get("runs_last_6_balls", 0)
        runs_last_12  = data.get("runs_last_12_balls", 0)
        wickets_last_6  = data.get("wickets_last_6_balls", 0)
        wickets_last_12 = data.get("wickets_last_12_balls", 0)
        boundaries_last_6  = data.get("boundaries_last_6_balls", 0)
        boundaries_last_12 = data.get("boundaries_last_12_balls", 0)
        dot_balls_last_6  = data.get("dot_balls_last_6_balls", 0)
        dot_balls_last_12 = data.get("dot_balls_last_12_balls", 0)

        # ── Derived momentum features from rolling windows ────────────
        # These were previously hardcoded to 0, which degraded predictions.
        # Computed the same way they were during model training.
        boundary_momentum  = boundaries_last_12 * 4          # boundary run contribution
        dot_ball_pressure  = (dot_balls_last_12 / 12 * 100) if dot_balls_last_12 > 0 else 0.0
        momentum_score     = (runs_last_6 - (wickets_last_6 * 8)) / max(1, 6)
        pressure_index     = rrr + (wickets_last_6 * 2) + (dot_ball_pressure / 10)

        # Lookup batter/bowler/team/venue stats from reference DataFrames
        batter_stats = self._lookup_player(data.get("batter_name", "Unknown"))
        bowler_stats = self._lookup_player(data.get("bowler_name", "Unknown"))
        team_stats   = self._lookup_team(data.get("batting_team", ""))
        venue_stats  = self._lookup_venue(data.get("venue", ""))

        row = {
            "Match_ID": "API_REQUEST",
            "Season": data.get("season", DEFAULT_SEASON),
            "Venue": data.get("venue", "Unknown"),
            "Batting_Team": data.get("batting_team", ""),
            "Bowling_Team": data.get("bowling_team", ""),
            "Innings": int(data.get("innings", 1)),
            "Current_Over": over,
            "Current_Ball": data.get("current_ball", 0),
            "Current_Score": current_score,
            "Current_Wickets": data.get("current_wickets", 0),
            "Balls_Remaining": balls_remaining,
            "Overs_Remaining": overs_remaining,
            "Runs_Remaining": runs_remaining,
            "Target": target,
            "Current_Run_Rate": round(crr, 2),
            "Required_Run_Rate": round(rrr, 2),
            "Required_Run_Rate_Gap": round(rrr - crr, 2),
            # Rolling features
            "Runs_Last_6_Balls": runs_last_6,
            "Runs_Last_12_Balls": runs_last_12,
            "Runs_Last_18_Balls": data.get("runs_last_18_balls", 0),
            "Runs_Last_30_Balls": data.get("runs_last_30_balls", 0),
            "Wickets_Last_6_Balls": wickets_last_6,
            "Wickets_Last_12_Balls": wickets_last_12,
            "Boundaries_Last_6_Balls": boundaries_last_6,
            "Boundaries_Last_12_Balls": boundaries_last_12,
            "Dot_Balls_Last_6_Balls": dot_balls_last_6,
            "Dot_Balls_Last_12_Balls": dot_balls_last_12,
            # Momentum features — now computed from rolling windows, not hardcoded to 0
            "Momentum_Score": round(momentum_score, 4),
            "Boundary_Momentum": boundary_momentum,
            "Dot_Ball_Pressure": round(dot_ball_pressure, 2),
            "Pressure_Index": round(pressure_index, 4),
            "Current_Partnership_Runs": 0,
            "Current_Partnership_Balls": 0,
            "Current_Partnership_Run_Rate": 0,
            # Batter
            "Batter_Name": data.get("batter_name", "Unknown"),
            "Batter_Career_Average": batter_stats.get("Average", 0),
            "Batter_Career_Strike_Rate": batter_stats.get("Strike_Rate", 0),
            "Batter_Recent_Form": batter_stats.get("Average", 0),
            "Batter_Boundary_Percentage": batter_stats.get("Boundary_Percentage", 0),
            "Batting_Impact_Score": batter_stats.get("Batting_Impact_Score", 0),
            # Bowler
            "Bowler_Name": data.get("bowler_name", "Unknown"),
            "Bowler_Economy": bowler_stats.get("Economy", 0),
            "Bowler_Strike_Rate": bowler_stats.get("Bowling_Strike_Rate", 0),
            "Bowler_Wicket_Rate": (
                1 / bowler_stats["Bowling_Strike_Rate"]
                if bowler_stats.get("Bowling_Strike_Rate", 0) > 0 else 0
            ),
            "Bowler_Recent_Form": bowler_stats.get("Economy", 0),
            "Bowler_Dot_Ball_Percentage": (
                bowler_stats.get("Dot_Balls_Bowled", 0) / bowler_stats.get("Balls_Bowled", 1) * 100
                if bowler_stats.get("Balls_Bowled", 0) > 0 else 0
            ),
            "Bowling_Impact_Score": bowler_stats.get("Bowling_Impact_Score", 0),
            # Team
            "Team_Win_Percentage": team_stats.get("Win_Percentage", 50),
            "Bat_First_Strength": team_stats.get("Bat_First_Win_Percentage", 0),
            "Chase_Strength": team_stats.get("Chasing_Win_Percentage", 0),
            "Team_Form_Last_5_Matches": team_stats.get("Win_Percentage", 50),
            # Venue
            "Venue_Run_Rate": venue_stats.get("Average_Run_Rate", 8.0),
            "Venue_Average_Score": venue_stats.get("Average_First_Innings", 160),
            "Venue_Chasing_Success": venue_stats.get("Chasing_Win_Percentage", 50),
            "Venue_Difficulty_Index": max(0, 10 - venue_stats.get("Average_Run_Rate", 8.0)),
            # Phase flags
            "Powerplay_Flag": 1 if over < 6 else 0,
            "Middle_Overs_Flag": 1 if 6 <= over < 15 else 0,
            "Death_Overs_Flag": 1 if over >= 15 else 0,
            "Pressure_Overs_Flag": 1 if overs_remaining <= 3 else 0,
        }
        return pd.DataFrame([row])

    def predict_momentum(self, feature_row: pd.DataFrame) -> Dict[str, Any]:
        """Run momentum model on a feature row. Returns class, probs, confidence."""
        df = self.encode(feature_row, self.momentum_features, self.momentum_encoders)
        pred = int(self.momentum_model.predict(df)[0])
        proba = self.momentum_model.predict_proba(df)[0]
        return {
            "momentum_class": MOMENTUM_LABELS.get(pred, "Unknown"),
            "probabilities": {MOMENTUM_LABELS[i]: round(float(p), 4) for i, p in enumerate(proba)},
            "confidence": round(float(np.max(proba)), 4),
        }

    def predict_win(self, feature_row: pd.DataFrame, batting_team: str, bowling_team: str) -> Dict[str, Any]:
        """Run win model on a feature row. Returns win probs, winner, confidence."""
        df = self.encode(feature_row, self.win_features, self.win_encoders)
        proba = self.win_model.predict_proba(df)[0]
        win_pct = round(float(proba[1]) * 100, 2)
        loss_pct = round(float(proba[0]) * 100, 2)
        winner = batting_team if win_pct >= 50 else bowling_team
        confidence = round(float(np.max(proba)), 4)
        return {
            "team_a": batting_team,
            "team_b": bowling_team,
            "win_probability": {batting_team: win_pct, bowling_team: loss_pct},
            "predicted_winner": winner,
            "confidence": confidence,
        }

    def encode(self, df: pd.DataFrame, feature_cols: list, encoders: dict) -> pd.DataFrame:
        """
        Apply label encoding — mirrors predict.py logic exactly.
        Public method (previously _encode) so routes don't call private internals.
        """
        df = df.copy()
        str_cols = df.select_dtypes(include=["object"]).columns.tolist()
        for col in str_cols:
            if col in encoders:
                le = encoders[col]
                df[col] = df[col].fillna("Missing").astype(str)
                df[col] = df[col].map(lambda s, _le=le: s if s in _le.classes_ else _le.classes_[0])
                df[col] = le.transform(df[col])
            else:
                # Force remaining object columns to numeric (LightGBM requirement)
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        df = df.fillna(0).replace([np.inf, -np.inf], 0)
        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0
        return df[feature_cols]

    # Keep _encode as an alias for any internal code that still uses the private name
    _encode = encode

    def _lookup_player(self, name: str) -> dict:
        if self.player_stats is None or name in ("", "Unknown"):
            return {}
        match = self.player_stats[self.player_stats["Player_Name"] == name]
        return match.iloc[0].to_dict() if not match.empty else {}

    def _lookup_team(self, name: str) -> dict:
        if self.team_stats is None or name == "":
            return {}
        match = self.team_stats[self.team_stats["Team"] == name]
        return match.iloc[0].to_dict() if not match.empty else {}

    def _lookup_venue(self, name: str) -> dict:
        if self.venue_stats is None or name in ("", "Unknown"):
            return {}
        match = self.venue_stats[self.venue_stats["Venue"] == name]
        return match.iloc[0].to_dict() if not match.empty else {}


# ── Global singleton ─────────────────────────────────────────────────
model_store = ModelStore()
