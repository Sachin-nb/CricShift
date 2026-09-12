"""
What-If Match Simulation Engine — Phase 3C
============================================
Allows hypothetical changes to a match state and re-runs the
trained Momentum and Win Prediction models to compare outcomes.

Supported what-if modifications:
  • Replace Batter / Bowler
  • Change current runs, wickets, venue, teams
  • Modify overs remaining, required runs, target
  • Change batting/bowling order (via player stats swap)

Outputs:
  • Original vs modified predictions
  • Win probability delta
  • Momentum delta
  • Textual explanation of the change impact
"""

import json
import logging
import pickle
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

MOMENTUM_LABELS = {0: "Negative", 1: "Neutral", 2: "Positive"}


# ── Model helpers (reuse exact logic from predict.py) ─────────────────────────
def _load_model_assets(model_dir: Path):
    with open(model_dir / "best_model.pkl", "rb") as f:
        model = pickle.load(f)
    with open(model_dir / "feature_columns.pkl", "rb") as f:
        feature_cols = pickle.load(f)
    with open(model_dir / "label_encoder.pkl", "rb") as f:
        encoders = pickle.load(f)
    return model, feature_cols, encoders


def _predict_row(model, feature_cols: list, encoders: dict,
                 row_df: pd.DataFrame) -> Tuple[int, np.ndarray]:
    """Run prediction on a single-row DataFrame, returning (predicted_class, probabilities)."""
    df = row_df.copy()
    str_cols = df.select_dtypes(include=["object"]).columns.tolist()
    for col in str_cols:
        if col in encoders:
            le = encoders[col]
            df[col] = df[col].fillna("Missing").astype(str)
            df[col] = df[col].map(lambda s, _le=le: s if s in _le.classes_ else _le.classes_[0])
            df[col] = le.transform(df[col])
    df = df.fillna(0).replace([np.inf, -np.inf], 0)
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
    X = df[feature_cols]
    pred = int(model.predict(X)[0])
    proba = model.predict_proba(X)[0]
    return pred, proba


class SimulationEngine:
    """What-if match simulation engine."""

    def __init__(self, player_stats_path: Optional[Path] = None):
        self.momentum_dir = PROJECT_ROOT / "models" / "momentum"
        self.win_dir = PROJECT_ROOT / "models" / "win_prediction"
        self.player_stats_path = player_stats_path or (
            PROJECT_ROOT / "data" / "processed" / "player_stats.csv"
        )

        self.mom_model = None
        self.mom_features: list = []
        self.mom_encoders: dict = {}
        self.win_model = None
        self.win_features: list = []
        self.win_encoders: dict = {}
        self.player_stats: Optional[pd.DataFrame] = None

    def load(self) -> None:
        """Load both models and player stats."""
        logger.info("Loading simulation assets …")
        self.mom_model, self.mom_features, self.mom_encoders = _load_model_assets(self.momentum_dir)
        self.win_model, self.win_features, self.win_encoders = _load_model_assets(self.win_dir)
        self.player_stats = pd.read_csv(self.player_stats_path)
        logger.info("  → Models and player stats loaded")

    # ── Core: run a single what-if scenario ──────────────────────────────
    def simulate(self, original_row: pd.Series, modifications: Dict[str, Any],
                 scenario_name: str = "") -> Dict[str, Any]:
        """
        Apply *modifications* to *original_row*, re-run both models,
        and return a comparison dict.

        Parameters
        ----------
        original_row : pd.Series
            A single row from the feature dataset.
        modifications : dict
            Keys can be any feature column name, or special keys:
            - "replace_batter": new batter name
            - "replace_bowler": new bowler name
        scenario_name : str
            Human label for this scenario.
        """
        original_df = pd.DataFrame([original_row])
        modified_df = pd.DataFrame([original_row.copy()])

        change_descriptions = []

        for key, value in modifications.items():
            if key == "replace_batter":
                modified_df, desc = self._replace_batter(modified_df, value)
                change_descriptions.append(desc)
            elif key == "replace_bowler":
                modified_df, desc = self._replace_bowler(modified_df, value)
                change_descriptions.append(desc)
            elif key in modified_df.columns:
                old_val = modified_df[key].iloc[0]
                modified_df[key] = value
                change_descriptions.append(f"{key}: {old_val} → {value}")
                # Recalculate derived columns if applicable
                modified_df = self._recalculate_derived(modified_df, key)
            else:
                logger.warning(f"Unknown modification key: {key}")

        # ── Run both models on original ──────────────────────────────────
        orig_mom_pred, orig_mom_proba = _predict_row(
            self.mom_model, self.mom_features, self.mom_encoders, original_df
        )
        orig_win_pred, orig_win_proba = _predict_row(
            self.win_model, self.win_features, self.win_encoders, original_df
        )

        # ── Run both models on modified ──────────────────────────────────
        new_mom_pred, new_mom_proba = _predict_row(
            self.mom_model, self.mom_features, self.mom_encoders, modified_df
        )
        new_win_pred, new_win_proba = _predict_row(
            self.win_model, self.win_features, self.win_encoders, modified_df
        )

        orig_win_pct = round(float(orig_win_proba[1]) * 100, 2)
        new_win_pct = round(float(new_win_proba[1]) * 100, 2)
        win_delta = round(new_win_pct - orig_win_pct, 2)

        mom_delta = new_mom_pred - orig_mom_pred

        explanation = self._generate_explanation(
            change_descriptions, orig_win_pct, new_win_pct, win_delta,
            orig_mom_pred, new_mom_pred, mom_delta
        )

        return {
            "scenario_name": scenario_name,
            "modifications": modifications,
            "change_descriptions": change_descriptions,
            "original": {
                "win_probability_pct": orig_win_pct,
                "momentum_class": orig_mom_pred,
                "momentum_label": MOMENTUM_LABELS.get(orig_mom_pred, "Unknown"),
                "momentum_probabilities": {
                    MOMENTUM_LABELS[i]: round(float(p), 4)
                    for i, p in enumerate(orig_mom_proba)
                },
                "win_probabilities": {
                    "Loss": round(float(orig_win_proba[0]), 4),
                    "Win": round(float(orig_win_proba[1]), 4),
                },
            },
            "modified": {
                "win_probability_pct": new_win_pct,
                "momentum_class": new_mom_pred,
                "momentum_label": MOMENTUM_LABELS.get(new_mom_pred, "Unknown"),
                "momentum_probabilities": {
                    MOMENTUM_LABELS[i]: round(float(p), 4)
                    for i, p in enumerate(new_mom_proba)
                },
                "win_probabilities": {
                    "Loss": round(float(new_win_proba[0]), 4),
                    "Win": round(float(new_win_proba[1]), 4),
                },
            },
            "delta": {
                "win_probability_delta": win_delta,
                "momentum_delta": int(mom_delta),
                "momentum_shift": (
                    f"{MOMENTUM_LABELS.get(orig_mom_pred, '?')} → "
                    f"{MOMENTUM_LABELS.get(new_mom_pred, '?')}"
                ),
            },
            "explanation": explanation,
        }

    # ── Batch simulation ─────────────────────────────────────────────────
    def simulate_batch(
        self, original_row: pd.Series,
        scenarios: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Run multiple what-if scenarios against the same baseline row."""
        results = []
        for sc in scenarios:
            result = self.simulate(
                original_row,
                sc.get("modifications", {}),
                sc.get("name", ""),
            )
            results.append(result)
        return results

    # ── Player replacement helpers ────────────────────────────────────────
    def _replace_batter(self, df: pd.DataFrame, new_batter: str) -> Tuple[pd.DataFrame, str]:
        old_batter = df["Batter_Name"].iloc[0] if "Batter_Name" in df.columns else "Unknown"
        df["Batter_Name"] = new_batter

        stats = self._lookup_player(new_batter)
        if stats is not None:
            df["Batter_Career_Average"] = stats.get("Average", 0)
            df["Batter_Career_Strike_Rate"] = stats.get("Strike_Rate", 0)
            df["Batter_Boundary_Percentage"] = stats.get("Boundary_Percentage", 0)
            df["Batting_Impact_Score"] = stats.get("Batting_Impact_Score", 0)
            if "Batter_Recent_Form" in df.columns:
                df["Batter_Recent_Form"] = stats.get("Average", 0)

        return df, f"Batter: {old_batter} → {new_batter}"

    def _replace_bowler(self, df: pd.DataFrame, new_bowler: str) -> Tuple[pd.DataFrame, str]:
        old_bowler = df["Bowler_Name"].iloc[0] if "Bowler_Name" in df.columns else "Unknown"
        df["Bowler_Name"] = new_bowler

        stats = self._lookup_player(new_bowler)
        if stats is not None:
            df["Bowler_Economy"] = stats.get("Economy", 0)
            df["Bowler_Strike_Rate"] = stats.get("Bowling_Strike_Rate", 0)
            bsr = stats.get("Bowling_Strike_Rate", 0)
            df["Bowler_Wicket_Rate"] = 1 / bsr if bsr > 0 else 0
            bb = stats.get("Balls_Bowled", 0)
            dbb = stats.get("Dot_Balls_Bowled", 0)
            df["Bowler_Dot_Ball_Percentage"] = (dbb / bb * 100) if bb > 0 else 0
            df["Bowling_Impact_Score"] = stats.get("Bowling_Impact_Score", 0)
            if "Bowler_Recent_Form" in df.columns:
                df["Bowler_Recent_Form"] = stats.get("Economy", 0)

        return df, f"Bowler: {old_bowler} → {new_bowler}"

    def _lookup_player(self, name: str) -> Optional[Dict]:
        if self.player_stats is None:
            return None
        match = self.player_stats[self.player_stats["Player_Name"] == name]
        if match.empty:
            logger.warning(f"  Player '{name}' not found in stats — using defaults")
            return None
        return match.iloc[0].to_dict()

    def _recalculate_derived(self, df: pd.DataFrame, changed_key: str) -> pd.DataFrame:
        """Recalculate dependent columns when a base column changes."""
        if changed_key in ("Current_Score", "Current_Over", "Current_Ball"):
            balls = df["Current_Over"].iloc[0] * 6 + df["Current_Ball"].iloc[0]
            if balls > 0:
                df["Current_Run_Rate"] = (df["Current_Score"].iloc[0] / balls) * 6
            df["Balls_Remaining"] = max(0, 120 - balls)
            df["Overs_Remaining"] = df["Balls_Remaining"].iloc[0] / 6

        if changed_key in ("Current_Score", "Target"):
            target = df["Target"].iloc[0]
            if target > 0:
                df["Runs_Remaining"] = max(0, target - df["Current_Score"].iloc[0])
                br = df["Balls_Remaining"].iloc[0]
                df["Required_Run_Rate"] = (df["Runs_Remaining"].iloc[0] / br * 6) if br > 0 else 0
                df["Required_Run_Rate_Gap"] = df["Required_Run_Rate"].iloc[0] - df["Current_Run_Rate"].iloc[0]

        if changed_key == "Current_Wickets":
            wickets = df["Current_Wickets"].iloc[0]
            df["Pressure_Index"] = df["Required_Run_Rate"].iloc[0] + wickets * 3

        return df

    def _generate_explanation(
        self, changes: List[str],
        orig_win: float, new_win: float, win_delta: float,
        orig_mom: int, new_mom: int, mom_delta: int
    ) -> str:
        """Generate a natural-language explanation of the simulation result."""
        parts = [f"Changes applied: {'; '.join(changes)}."]

        if abs(win_delta) < 1:
            parts.append(f"Win probability barely changed ({orig_win}% → {new_win}%).")
        elif win_delta > 0:
            parts.append(
                f"Win probability INCREASED by {win_delta:+.2f}pp "
                f"({orig_win}% → {new_win}%). This change favours the batting team."
            )
        else:
            parts.append(
                f"Win probability DECREASED by {win_delta:+.2f}pp "
                f"({orig_win}% → {new_win}%). This change favours the bowling team."
            )

        if mom_delta == 0:
            parts.append(f"Momentum remained {MOMENTUM_LABELS.get(orig_mom, 'unchanged')}.")
        else:
            parts.append(
                f"Momentum shifted from {MOMENTUM_LABELS.get(orig_mom, '?')} to "
                f"{MOMENTUM_LABELS.get(new_mom, '?')}."
            )

        return " ".join(parts)
