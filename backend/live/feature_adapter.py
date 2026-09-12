"""
LiveFeatureAdapter — transforms the normalised live-state dict into the
feature DataFrame expected by the Phase-3 ML models.

Key normaliser keys consumed here:
    current_score, current_wickets, overs, batting_team, bowling_team,
    innings, target, recent_overs, current_striker, current_bowler,
    partnership_runs, partnership_balls, venue, season
"""

import logging
import pickle
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from . import matcher

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class LiveFeatureAdapter:
    def __init__(self):
        encoder_path       = BASE_DIR / "models" / "momentum"       / "label_encoder.pkl"
        momentum_cols_path = BASE_DIR / "models" / "momentum"       / "feature_columns.pkl"
        win_cols_path      = BASE_DIR / "models" / "win_prediction" / "feature_columns.pkl"

        with open(encoder_path, "rb") as f:
            self.encoders = pickle.load(f)
        with open(momentum_cols_path, "rb") as f:
            self.momentum_features = pickle.load(f)
        with open(win_cols_path, "rb") as f:
            self.win_features = pickle.load(f)

    # ── cricket overs helper ─────────────────────────────────────────────────
    @staticmethod
    def parse_cricket_overs(overs_float: float):
        """
        Convert cricket notation float → (completed_overs, balls_in_over, total_balls).
        e.g.  15.4  →  (15, 4, 94)
        """
        try:
            overs_str = f"{float(overs_float):.1f}"
        except (ValueError, TypeError):
            overs_str = "0.0"
        parts = overs_str.split(".")
        completed  = int(parts[0])
        ball_digit = int(parts[1]) if len(parts) > 1 else 0
        # clamp: API occasionally sends .7 before rollover
        ball_digit = min(ball_digit, 6)
        total = completed * 6 + ball_digit
        return completed, ball_digit, total

    # ── ball-string helpers ──────────────────────────────────────────────────
    @staticmethod
    def _runs(b: str) -> int:
        b_up = b.upper()
        if b_up in ("W", "WICKET"):
            return 0
        if b_up in ("NB", "WD", "NO-BALL", "WIDE"):
            return 1
        try:
            return int(b)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _is_wicket(b: str) -> int:
        return 1 if b.upper() in ("W", "WICKET") else 0

    @staticmethod
    def _is_boundary(b: str) -> int:
        try:
            return 1 if int(b) in (4, 6) else 0
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _is_dot(b: str) -> int:
        b_up = b.upper()
        if b_up in ("W", "WICKET", "NB", "WD", "NO-BALL", "WIDE"):
            return 0
        try:
            return 1 if int(b) == 0 else 0
        except (ValueError, TypeError):
            return 0

    # ── main transform ───────────────────────────────────────────────────────
    def process_live_payload(self, live_data: dict) -> pd.DataFrame:
        """
        Produce a single-row feature DataFrame from a normalised live-state dict.

        Accepts BOTH normaliser key names (current_score / current_wickets / overs)
        and legacy names (score / wickets) so old call-sites keep working.
        """
        # ── season / venue / teams ───────────────────────────────────────
        season       = str(live_data.get("season", str(datetime.now().year)))
        venue        = live_data.get("venue", "Unknown") or "Unknown"
        batting_team = live_data.get("batting_team", "Unknown") or "Unknown"
        bowling_team = live_data.get("bowling_team", "Unknown") or "Unknown"

        # ── score & wickets — accept both key naming conventions ─────────
        current_score   = int(
            live_data.get("current_score") or live_data.get("score") or 0
        )
        current_wickets = int(
            live_data.get("current_wickets") or live_data.get("wickets") or 0
        )

        # ── overs — normaliser always writes "overs" ─────────────────────
        overs_raw = float(live_data.get("overs", 0.0) or 0.0)
        current_over, current_ball, balls_bowled = self.parse_cricket_overs(overs_raw)

        balls_remaining = max(0, 120 - balls_bowled)
        overs_remaining = balls_remaining / 6

        # ── innings — prefer explicit key, fall back to target heuristic ─
        target = int(live_data.get("target", 0) or 0)
        innings = int(live_data.get("innings", 2 if target > 0 else 1) or 1)

        runs_remaining = max(0, target - current_score) if innings == 2 else 0

        crr = (current_score / balls_bowled * 6) if balls_bowled > 0 else 0.0
        rrr = (runs_remaining / balls_remaining * 6) if innings == 2 and balls_remaining > 0 else 0.0
        rrr_gap = rrr - crr if innings == 2 else 0.0

        # ── phase flags ───────────────────────────────────────────────────
        powerplay_flag    = 1 if current_over < 6  else 0
        middle_overs_flag = 1 if 6  <= current_over < 15 else 0
        death_overs_flag  = 1 if current_over >= 15 else 0
        pressure_overs_flag = 1 if overs_remaining <= 3 else 0

        # ── rolling features from recent_overs string ────────────────────
        recent_str  = str(live_data.get("recent_overs", "") or "")
        balls_list  = recent_str.split() if recent_str else []

        def _slice(n):
            return balls_list[-n:] if len(balls_list) >= n else balls_list

        b6  = _slice(6)
        b12 = _slice(12)
        b18 = _slice(18)
        b30 = _slice(30)

        runs_last_6  = sum(self._runs(b) for b in b6)
        runs_last_12 = sum(self._runs(b) for b in b12)
        runs_last_18 = sum(self._runs(b) for b in b18)
        runs_last_30 = sum(self._runs(b) for b in b30)

        wickets_last_6  = sum(self._is_wicket(b) for b in b6)
        wickets_last_12 = sum(self._is_wicket(b) for b in b12)

        bound_last_6  = sum(self._is_boundary(b) for b in b6)
        bound_last_12 = sum(self._is_boundary(b) for b in b12)

        dot_last_6  = sum(self._is_dot(b) for b in b6)
        dot_last_12 = sum(self._is_dot(b) for b in b12)

        dot_ball_pressure = (dot_last_12 / 12 * 100) if b12 else 0.0
        pressure_index    = rrr + (wickets_last_6 * 2) + (dot_ball_pressure / 10)
        boundary_momentum = bound_last_12 * 4
        momentum_score    = (runs_last_6 - wickets_last_6 * 8) / max(1, 6)

        # ── partnership ──────────────────────────────────────────────────
        p_runs  = int(live_data.get("partnership_runs", 0) or 0)
        p_balls = int(live_data.get("partnership_balls", 1) or 1)
        p_rr    = (p_runs / p_balls * 6) if p_balls > 0 else 0.0

        # ── historical look-ups (SQLite via matcher) ─────────────────────
        batter = str(live_data.get("current_striker", "") or "Unknown")
        bowler = str(live_data.get("current_bowler",  "") or "Unknown")

        p_stats = matcher.get_player_stats(batter)
        b_stats = matcher.get_player_stats(bowler)
        t_stats = matcher.get_team_stats(batting_team)
        v_stats = matcher.get_venue_stats(venue)

        bb = b_stats.get("Balls_Bowled", 0)
        dbb = b_stats.get("Dot_Balls_Bowled", 0)
        bsr = b_stats.get("Bowling_Strike_Rate", 0)

        features = {
            # Identity / meta
            "Season":       season,
            "Venue":        venue,
            "Batting_Team": batting_team,
            "Bowling_Team": bowling_team,
            "Innings":      innings,

            # Over / ball position
            "Current_Over":  current_over,
            "Current_Ball":  current_ball,

            # Score state
            "Current_Score":   current_score,
            "Current_Wickets": current_wickets,
            "Target":          target,

            # Derived rate features
            "Current_Run_Rate":      round(crr,     4),
            "Required_Run_Rate":     round(rrr,     4),
            "Required_Run_Rate_Gap": round(rrr_gap, 4),
            "Balls_Remaining":       balls_remaining,
            "Overs_Remaining":       round(overs_remaining, 4),
            "Runs_Remaining":        runs_remaining,

            # Rolling windows
            "Runs_Last_6_Balls":       runs_last_6,
            "Runs_Last_12_Balls":      runs_last_12,
            "Runs_Last_18_Balls":      runs_last_18,
            "Runs_Last_30_Balls":      runs_last_30,
            "Wickets_Last_6_Balls":    wickets_last_6,
            "Wickets_Last_12_Balls":   wickets_last_12,
            "Boundaries_Last_6_Balls": bound_last_6,
            "Boundaries_Last_12_Balls": bound_last_12,
            "Dot_Balls_Last_6_Balls":  dot_last_6,
            "Dot_Balls_Last_12_Balls": dot_last_12,

            # Pressure / momentum derived
            "Pressure_Index":    round(pressure_index,    4),
            "Boundary_Momentum": boundary_momentum,
            "Dot_Ball_Pressure": round(dot_ball_pressure, 4),
            "Momentum_Score":    round(momentum_score,    4),

            # Partnership
            "Current_Partnership_Runs":     p_runs,
            "Current_Partnership_Balls":    p_balls,
            "Current_Partnership_Run_Rate": round(p_rr, 4),

            # Batter stats
            "Batter_Name":               batter,
            "Batter_Career_Average":      p_stats.get("Average",            0),
            "Batter_Career_Strike_Rate":  p_stats.get("Strike_Rate",        0),
            "Batter_Recent_Form":         p_stats.get("Average",            0),
            "Batter_Boundary_Percentage": p_stats.get("Boundary_Percentage",0),
            "Batting_Impact_Score":       p_stats.get("Batting_Impact_Score",0),

            # Bowler stats
            "Bowler_Name":               bowler,
            "Bowler_Economy":            b_stats.get("Economy",             0),
            "Bowler_Strike_Rate":        bsr,
            "Bowler_Wicket_Rate":        (1 / bsr) if bsr > 0 else 0,
            "Bowler_Recent_Form":        b_stats.get("Economy",             0),
            "Bowler_Dot_Ball_Percentage":(dbb / bb * 100) if bb > 0 else 0,
            "Bowling_Impact_Score":      b_stats.get("Bowling_Impact_Score",0),

            # Team stats
            "Team_Win_Percentage":     t_stats.get("Win_Percentage",         50),
            "Bat_First_Strength":      t_stats.get("Bat_First_Win_Percentage",0),
            "Chase_Strength":          t_stats.get("Chasing_Win_Percentage", 0),
            "Team_Form_Last_5_Matches":t_stats.get("Win_Percentage",         50),

            # Venue stats
            "Venue_Run_Rate":        v_stats.get("Average_Run_Rate",       8.0),
            "Venue_Average_Score":   v_stats.get("Average_First_Innings", 160),
            "Venue_Chasing_Success": v_stats.get("Chasing_Win_Percentage", 50),
            "Venue_Difficulty_Index":max(0, 10 - v_stats.get("Average_Run_Rate", 8.0)),

            # Phase flags
            "Powerplay_Flag":     powerplay_flag,
            "Middle_Overs_Flag":  middle_overs_flag,
            "Death_Overs_Flag":   death_overs_flag,
            "Pressure_Overs_Flag":pressure_overs_flag,
        }

        df = pd.DataFrame([features])

        # ── Label-encode categorical columns ─────────────────────────────
        for col in df.select_dtypes(include=["object"]).columns.tolist():
            if col in self.encoders:
                le = self.encoders[col]
                val = str(df[col].iloc[0])
                if val not in le.classes_:
                    logger.debug(f"Unseen label '{val}' in '{col}' — using class[0]")
                    val = le.classes_[0]
                df[col] = le.transform([val])
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        df = df.fillna(0).replace([np.inf, -np.inf], 0)
        return df

    # ── feature-slice helpers ────────────────────────────────────────────────
    def _ensure_columns(self, df: pd.DataFrame, cols: list) -> pd.DataFrame:
        """Add any missing columns as 0 and return only the expected columns."""
        for c in cols:
            if c not in df.columns:
                df[c] = 0
        return df[cols].copy()

    def get_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._ensure_columns(df, self.momentum_features)

    def get_win_features(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._ensure_columns(df, self.win_features)
