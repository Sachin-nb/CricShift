"""
Feature Engineering Module
===========================
Computes rolling match features after every ball delivery.
Each feature captures a different aspect of match dynamics:

- Current Run Rate (CRR)
- Required Run Rate (RRR)  [2nd innings only]
- Runs in Last Over (rolling window)
- Wickets in Last N Balls
- Dot Ball Percentage
- Boundary Frequency
- Pressure Index (composite)
- Run Rate Acceleration

All features are computed incrementally and appended as new columns
to the ball-by-ball DataFrame.

Mathematical definitions:
  CRR = cumulative_runs / (balls_bowled / 6)
  RRR = (target - cumulative_runs) / (remaining_balls / 6)
  Dot% = (dot_balls_in_window / window_size) * 100
  Boundary% = (boundaries_in_window / window_size) * 100
  Pressure = f(RRR_gap, recent_wickets, dot%, cumulative_wickets, balls_remaining)
  Acceleration = recent_window_RR - overall_CRR
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


class FeatureEngine:
    """Compute rolling match features for each ball delivery."""

    def __init__(self, target_score: int = 0):
        """
        Initialize the feature engine.

        Args:
            target_score: Target score for 2nd innings (0 for 1st innings).
        """
        self.target_score = target_score

    def compute_features(self, df: pd.DataFrame, innings: int = 2) -> pd.DataFrame:
        """
        Compute all rolling features for the given innings data.

        Args:
            df: Ball-by-ball DataFrame for a single innings.
            innings: Which innings (1 or 2) this data represents.

        Returns:
            DataFrame with all feature columns added.
        """
        df = df.copy().reset_index(drop=True)

        # Core rate features
        df["current_run_rate"] = self._compute_crr(df)
        df["required_run_rate"] = self._compute_rrr(df, innings)

        # Rolling window features
        df["runs_last_over"] = self._rolling_sum(
            df["total_runs"], config.ROLLING_OVER_WINDOW
        )
        df["runs_last_5_overs"] = self._rolling_sum(
            df["total_runs"], config.ROLLING_5_OVER_WINDOW
        )
        df["wickets_last_n"] = self._rolling_sum(
            df["is_wicket"], config.WICKET_LOOKBACK_BALLS
        )
        df["dot_ball_pct"] = self._rolling_mean(
            df["is_dot"], config.DOT_BALL_WINDOW
        ) * 100
        df["boundary_freq"] = self._rolling_mean(
            df["is_boundary"], config.BOUNDARY_WINDOW
        ) * 100

        # Composite features
        df["pressure_index"] = self._compute_pressure_index(df, innings)
        df["run_rate_acceleration"] = self._compute_rr_acceleration(df)

        # Round all computed features for clean output
        for col in ["current_run_rate", "required_run_rate", "runs_last_over",
                     "runs_last_5_overs", "dot_ball_pct", "boundary_freq",
                     "pressure_index", "run_rate_acceleration"]:
            df[col] = df[col].round(2)

        return df

    def _compute_crr(self, df: pd.DataFrame) -> pd.Series:
        """
        Current Run Rate = cumulative_runs / (ball_number / 6).

        Handles edge case: first ball returns actual runs * 6 as the rate,
        which is mathematically correct (1 ball = 1/6 of an over).

        Returns:
            Series of CRR values, one per ball.
        """
        # ball_number is 1-indexed, so ball 1 = 1/6 of an over bowled
        overs_bowled = df["ball_number"].astype(float) / config.BALLS_PER_OVER
        # overs_bowled is never 0 since ball_number starts at 1
        crr = df["cumulative_runs"].astype(float) / overs_bowled
        return crr.fillna(0.0)

    def _compute_rrr(self, df: pd.DataFrame, innings: int) -> pd.Series:
        """
        Required Run Rate (only meaningful for 2nd innings).
        RRR = (target - cumulative_runs) / (remaining_balls / 6)

        Edge cases handled:
          - 1st innings: returns 0
          - Target already reached: returns 0
          - No balls remaining: returns 0 (match over)
          - Negative remaining runs: returns 0 (already won)

        Args:
            df: Ball-by-ball data.
            innings: Innings number.

        Returns:
            Series of RRR values.
        """
        if innings == 1 or self.target_score == 0:
            return pd.Series(0.0, index=df.index)

        remaining_runs = (self.target_score - df["cumulative_runs"]).astype(float)
        remaining_balls = (config.TOTAL_BALLS - df["ball_number"]).astype(float)
        remaining_overs = remaining_balls / config.BALLS_PER_OVER

        # Handle division by zero: when no balls remain, RRR is meaningless
        rrr = np.where(
            remaining_overs > 0,
            remaining_runs / remaining_overs,
            0.0
        )
        # Can't have negative RRR (already won or target achieved)
        rrr = np.clip(rrr, 0, None)

        return pd.Series(rrr, index=df.index)

    def _compute_pressure_index(self, df: pd.DataFrame, innings: int) -> pd.Series:
        """
        Composite Pressure Index (0-100 scale).
        Combines required rate pressure, recent wickets, dot balls,
        cumulative wickets, and balls remaining.

        Higher = more pressure on batting side.

        Formula:
          pressure = rate_pressure + wicket_pressure + dot_pressure
                   + cumulative_wicket_pressure + phase_pressure

        Each component is bounded and the total is capped at [0, 100].
        """
        pressure = pd.Series(0.0, index=df.index)
        balls_remaining = config.TOTAL_BALLS - df["ball_number"]

        # ── Component 1: Required rate pressure (2nd innings only) ──
        # How much harder is the required rate compared to current rate?
        if innings == 2 and self.target_score > 0:
            rrr = df.get("required_run_rate", pd.Series(0.0, index=df.index))
            crr = df.get("current_run_rate", pd.Series(0.0, index=df.index))
            rate_gap = (rrr - crr).clip(lower=0)
            # Scale: gap of 0 = 0 points, gap of 10+ = 25 points
            pressure += (rate_gap / config.PRESSURE_HIGH_RRR * 25).clip(upper=25)

        # ── Component 2: Recent wickets pressure ──
        # Each recent wicket adds PRESSURE_WICKET_WEIGHT points
        wickets_recent = self._rolling_sum(df["is_wicket"], config.WICKET_LOOKBACK_BALLS)
        pressure += (wickets_recent * config.PRESSURE_WICKET_WEIGHT).clip(upper=30)

        # ── Component 3: Dot ball pressure ──
        # High dot ball % in recent window increases pressure
        dot_pct = self._rolling_mean(df["is_dot"], config.PRESSURE_WINDOW) * 100
        # Scale: 0% dots = 0 pressure, 100% dots = 20 pressure
        pressure += (dot_pct / 100.0 * 20).clip(upper=20)

        # ── Component 4: Cumulative wickets pressure ──
        # Each total wicket lost adds incremental pressure
        # Non-linear: losing 8th wicket is more pressure than losing 1st
        wkt = df["cumulative_wickets"].astype(float)
        pressure += (wkt ** 1.3).clip(upper=15)

        # ── Component 5: Phase pressure (2nd innings) ──
        # Late in innings with runs to get = more pressure
        if innings == 2 and self.target_score > 0:
            remaining_runs = (self.target_score - df["cumulative_runs"]).clip(lower=0)
            overs_left = balls_remaining.astype(float) / config.BALLS_PER_OVER
            # If fewer overs left and still many runs needed, pressure rises
            runs_per_over_needed = np.where(
                overs_left > 0,
                remaining_runs / overs_left,
                0
            )
            phase_pressure = np.where(
                runs_per_over_needed > 12, 10,
                np.where(runs_per_over_needed > 9, 6,
                np.where(runs_per_over_needed > 7, 3, 0))
            )
            pressure += phase_pressure

        return pressure.clip(0, 100)

    def _compute_rr_acceleration(self, df: pd.DataFrame) -> pd.Series:
        """
        Run Rate Acceleration: difference between recent window run rate
        and overall CRR. Positive = scoring is accelerating.

        Formula:
          recent_rr = sum(runs in last N balls) / (N / 6)
          acceleration = recent_rr - overall_crr

        For early balls (fewer than window size), uses all available balls
        via min_periods=1, so the calculation is still valid.
        """
        window = config.RUN_RATE_ACCEL_WINDOW
        recent_runs = self._rolling_sum(df["total_runs"], window)

        # Actual window size used (min of window and balls bowled so far)
        actual_window = df["ball_number"].clip(upper=window).astype(float)
        recent_rr = recent_runs / (actual_window / config.BALLS_PER_OVER)

        overall_rr = df["current_run_rate"]
        acceleration = recent_rr - overall_rr
        return acceleration

    @staticmethod
    def _rolling_sum(series: pd.Series, window: int) -> pd.Series:
        """Compute rolling sum with minimum period of 1."""
        return series.rolling(window=window, min_periods=1).sum()

    @staticmethod
    def _rolling_mean(series: pd.Series, window: int) -> pd.Series:
        """Compute rolling mean with minimum period of 1."""
        return series.rolling(window=window, min_periods=1).mean()
