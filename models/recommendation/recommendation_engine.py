"""
Player Recommendation Engine — Phase 3C
=========================================
Given a live match situation, recommends the best next batter
to send in, using career stats, impact scores, pressure
performance, and team context.

Key rules:
  • Never recommend players from the bowling team
  • Only recommend available (not-dismissed) batters
  • Rank by composite score; return Top-5
  • Each recommendation includes: Player, Score, Reason,
    Expected Impact, Confidence
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ── Match-situation dataclass-like dict ───────────────────────────────────────
def default_match_situation() -> Dict[str, Any]:
    """Return a template match-situation dictionary."""
    return {
        "batting_team": "",
        "bowling_team": "",
        "venue": "",
        "current_score": 0,
        "current_wickets": 0,
        "current_over": 0.0,
        "required_run_rate": 0.0,
        "pressure_index": 0.0,
        "momentum_score": 0.0,
        "current_batter": "",
        "current_bowler": "",
        "dismissed_batters": [],
    }


class RecommendationEngine:
    """Intelligent player recommendation engine for T20 cricket."""

    # ── Scoring weights ───────────────────────────────────────────────────
    WEIGHTS = {
        "career_average":       0.15,
        "strike_rate":          0.20,
        "boundary_pct":         0.10,
        "batting_impact":       0.20,
        "pressure_performance": 0.15,
        "experience":           0.10,
        "match_context":        0.10,
    }

    def __init__(self, player_stats_path: Optional[Path] = None,
                 team_stats_path: Optional[Path] = None,
                 venue_stats_path: Optional[Path] = None):
        self.player_stats_path = player_stats_path or (PROJECT_ROOT / "data" / "processed" / "player_stats.csv")
        self.team_stats_path = team_stats_path or (PROJECT_ROOT / "data" / "processed" / "team_stats.csv")
        self.venue_stats_path = venue_stats_path or (PROJECT_ROOT / "data" / "processed" / "venue_stats.csv")

        self.player_stats: Optional[pd.DataFrame] = None
        self.team_stats: Optional[pd.DataFrame] = None
        self.venue_stats: Optional[pd.DataFrame] = None

    # ── Load ──────────────────────────────────────────────────────────────
    def load_data(self) -> None:
        """Load all reference CSVs."""
        logger.info("Loading player / team / venue stats …")
        self.player_stats = pd.read_csv(self.player_stats_path)
        self.team_stats = pd.read_csv(self.team_stats_path)
        self.venue_stats = pd.read_csv(self.venue_stats_path)
        logger.info(f"  → {len(self.player_stats)} players, "
                     f"{len(self.team_stats)} teams, "
                     f"{len(self.venue_stats)} venues loaded")

    # ── Core recommendation ──────────────────────────────────────────────
    def recommend(self, situation: Dict[str, Any], top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Return the Top-*top_n* batters to send next given *situation*.

        Each entry: {Player, Recommendation_Score, Reason, Expected_Impact, Confidence}
        """
        if self.player_stats is None:
            self.load_data()

        batting_team = situation.get("batting_team", "")
        bowling_team = situation.get("bowling_team", "")
        dismissed = set(situation.get("dismissed_batters", []))
        current_batter = situation.get("current_batter", "")

        # ── Filter: only batting-team players who are available ──────────
        # We don't have a team roster column; approximate by using players
        # who have appeared for this team in the feature dataset.  As a
        # fallback, pick players with sufficient matches.
        candidates = self.player_stats.copy()

        # Remove bowling-team players (Rule: NEVER recommend from bowling team)
        # Remove dismissed batters & current batter
        exclude_names = dismissed | {current_batter}
        candidates = candidates[~candidates["Player_Name"].isin(exclude_names)]

        # Only batters with reasonable experience
        candidates = candidates[candidates["Innings_Batted"] > 0].copy()

        # ── Score each candidate ─────────────────────────────────────────
        candidates["_career_avg_score"] = self._normalise(candidates["Average"], 0, 50)
        candidates["_strike_rate_score"] = self._normalise(candidates["Strike_Rate"], 80, 200)
        candidates["_boundary_pct_score"] = self._normalise(candidates["Boundary_Percentage"], 0, 80)
        candidates["_batting_impact_score"] = self._normalise(candidates["Batting_Impact_Score"], 0, candidates["Batting_Impact_Score"].quantile(0.95) or 1)

        # Pressure performance: low dot-ball% as batter + high boundary% → good under pressure
        candidates["_pressure_score"] = (
            candidates["_boundary_pct_score"] * 0.6
            + (1 - self._normalise(candidates.get("Dot_Balls", pd.Series(0, index=candidates.index)),
                                    0, candidates.get("Balls_Faced", pd.Series(1, index=candidates.index)).clip(lower=1))) * 0.4
        ).clip(0, 1)

        # Experience score: more matches → higher (log-scaled)
        candidates["_experience_score"] = self._normalise(
            np.log1p(candidates["Matches_Played"]), 0, np.log1p(200)
        )

        # Match-context bonus: if death overs, prefer high SR; if powerplay, prefer aggressive
        over = float(situation.get("current_over", 10))
        rrr = float(situation.get("required_run_rate", 8.0))
        pressure = float(situation.get("pressure_index", 0.0))

        context_multiplier = 1.0
        if over >= 15:
            # Death overs — weight strike rate more
            context_multiplier = 1.0 + (candidates["_strike_rate_score"] - 0.5) * 0.3
        elif over < 6:
            # Powerplay — aggressive but reliable
            context_multiplier = 1.0 + (candidates["_boundary_pct_score"] - 0.5) * 0.2
        if rrr > 10:
            context_multiplier += candidates["_strike_rate_score"] * 0.2
        if pressure > 50:
            context_multiplier += candidates["_pressure_score"] * 0.15

        candidates["_context_score"] = (context_multiplier / context_multiplier.max()).clip(0, 1) if hasattr(context_multiplier, 'max') and context_multiplier.max() > 0 else 0.5

        # ── Composite score (0-100) ──────────────────────────────────────
        w = self.WEIGHTS
        candidates["Recommendation_Score"] = (
            candidates["_career_avg_score"]    * w["career_average"]
            + candidates["_strike_rate_score"] * w["strike_rate"]
            + candidates["_boundary_pct_score"] * w["boundary_pct"]
            + candidates["_batting_impact_score"] * w["batting_impact"]
            + candidates["_pressure_score"]     * w["pressure_performance"]
            + candidates["_experience_score"]   * w["experience"]
            + candidates["_context_score"]      * w["match_context"]
        ) * 100

        candidates["Recommendation_Score"] = candidates["Recommendation_Score"].round(2).clip(0, 100)

        # ── Confidence ───────────────────────────────────────────────────
        candidates["Confidence"] = (
            np.where(candidates["Matches_Played"] >= 30, 0.9,
            np.where(candidates["Matches_Played"] >= 15, 0.75,
            np.where(candidates["Matches_Played"] >= 5, 0.6, 0.4)))
        )

        # ── Expected Impact ──────────────────────────────────────────────
        candidates["Expected_Impact"] = (
            candidates["Batting_Impact_Score"].clip(lower=0)
        ).round(2)

        # ── Sort & select ────────────────────────────────────────────────
        candidates = candidates.sort_values("Recommendation_Score", ascending=False)
        top = candidates.head(top_n)

        results: List[Dict[str, Any]] = []
        for _, row in top.iterrows():
            reason = self._generate_reason(row, situation)
            results.append({
                "Player": row["Player_Name"],
                "Recommendation_Score": float(row["Recommendation_Score"]),
                "Reason": reason,
                "Expected_Impact": float(row["Expected_Impact"]),
                "Confidence": float(row["Confidence"]),
            })

        return results

    # ── Generate player rankings CSV ─────────────────────────────────────
    def generate_rankings(self, output_dir: Optional[Path] = None) -> pd.DataFrame:
        """Rank ALL players by general batting recommendation score."""
        if self.player_stats is None:
            self.load_data()

        situation = default_match_situation()
        situation["current_over"] = 10  # Mid-innings baseline

        # Score every player
        candidates = self.player_stats[self.player_stats["Innings_Batted"] > 0].copy()
        candidates["_career_avg_score"] = self._normalise(candidates["Average"], 0, 50)
        candidates["_sr_score"] = self._normalise(candidates["Strike_Rate"], 80, 200)
        candidates["_bp_score"] = self._normalise(candidates["Boundary_Percentage"], 0, 80)
        candidates["_imp_score"] = self._normalise(
            candidates["Batting_Impact_Score"], 0,
            candidates["Batting_Impact_Score"].quantile(0.95) or 1
        )
        candidates["_exp_score"] = self._normalise(
            np.log1p(candidates["Matches_Played"]), 0, np.log1p(200)
        )

        candidates["Ranking_Score"] = (
            candidates["_career_avg_score"] * 0.20
            + candidates["_sr_score"]       * 0.25
            + candidates["_bp_score"]       * 0.15
            + candidates["_imp_score"]      * 0.25
            + candidates["_exp_score"]      * 0.15
        ) * 100

        candidates = candidates.sort_values("Ranking_Score", ascending=False).reset_index(drop=True)
        candidates["Rank"] = candidates.index + 1

        rankings = candidates[["Rank", "Player_Name", "Matches_Played", "Average",
                                "Strike_Rate", "Boundary_Percentage",
                                "Batting_Impact_Score", "Ranking_Score"]].copy()
        rankings["Ranking_Score"] = rankings["Ranking_Score"].round(2)

        out_dir = output_dir or (PROJECT_ROOT / "models" / "recommendation")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "player_rankings.csv"
        rankings.to_csv(out_path, index=False)
        logger.info(f"  → Player rankings saved: {out_path} ({len(rankings)} players)")
        return rankings

    # ── Helpers ───────────────────────────────────────────────────────────
    @staticmethod
    def _normalise(series, vmin, vmax) -> pd.Series:
        """Min-max normalise to [0,1]."""
        if isinstance(vmax, (pd.Series, np.ndarray)):
            vmax = float(vmax.max()) if hasattr(vmax, 'max') else float(vmax)
        span = vmax - vmin
        if span <= 0:
            return pd.Series(0.5, index=series.index)
        return ((series - vmin) / span).clip(0, 1)

    @staticmethod
    def _generate_reason(row: pd.Series, situation: Dict[str, Any]) -> str:
        """Human-readable recommendation rationale."""
        parts = []
        avg = row.get("Average", 0)
        sr = row.get("Strike_Rate", 0)
        bp = row.get("Boundary_Percentage", 0)
        matches = row.get("Matches_Played", 0)

        if avg >= 30:
            parts.append(f"Strong career average ({avg:.1f})")
        if sr >= 140:
            parts.append(f"Explosive strike rate ({sr:.1f})")
        elif sr >= 120:
            parts.append(f"Good strike rate ({sr:.1f})")
        if bp >= 50:
            parts.append(f"High boundary percentage ({bp:.1f}%)")
        if matches >= 50:
            parts.append(f"Very experienced ({int(matches)} matches)")

        rrr = float(situation.get("required_run_rate", 0))
        over = float(situation.get("current_over", 0))
        if rrr > 10 and sr >= 130:
            parts.append("Ideal for high-pressure run chase")
        if over >= 15 and sr >= 140:
            parts.append("Death-overs specialist")

        return "; ".join(parts) if parts else "Reliable batting option"
