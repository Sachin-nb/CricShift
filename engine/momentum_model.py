"""
Momentum Model Module
======================
Calculates a dynamic Momentum Index after every ball delivery.
The index ranges from -100 (complete bowling dominance) to +100
(complete batting dominance).

The Momentum Index is a weighted composite of normalized feature
signals. Each signal is scaled to [-1, +1] range before weighting.

Signals:
  +1 direction = Batting dominance (high scoring, boundaries, acceleration)
  -1 direction = Bowling dominance (wickets, dots, high required rate)

Mathematical approach:
  Each raw feature is mapped to a [-1, +1] signal using carefully
  calibrated normalization functions based on real T20 cricket statistics:
  
  - Average T20 run rate: ~8.0 runs/over
  - Average T20 dot ball %: ~40%
  - Average T20 boundary %: ~15-20% of deliveries
  - Average T20 over yields: ~8 runs
  - Typical wicket rate: 1 per ~20 balls
  
  Final index = sum(signal_i * weight_i) * 100, clipped to [-100, +100]
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


class MomentumModel:
    """Calculate dynamic Momentum Index from computed features."""

    def __init__(self, weights: dict = None):
        """
        Initialize with optional custom weights.

        Args:
            weights: Dictionary of feature weights. Uses config defaults if None.
        """
        self.weights = weights or config.MOMENTUM_WEIGHTS

    def calculate(self, df: pd.DataFrame, innings: int = 2) -> pd.DataFrame:
        """
        Compute the Momentum Index for every ball in the DataFrame.

        Args:
            df: DataFrame with all features already computed.
            innings: Innings number (affects RRR-based signals).

        Returns:
            DataFrame with 'momentum_index' column added.
        """
        df = df.copy()

        # Compute individual signal components (each in [-1, +1])
        signals = {}

        signals["run_rate_factor"] = self._run_rate_signal(df, innings)
        signals["recent_scoring"] = self._recent_scoring_signal(df)
        signals["wicket_pressure"] = self._wicket_pressure_signal(df)
        signals["dot_ball_pressure"] = self._dot_ball_signal(df)
        signals["boundary_momentum"] = self._boundary_signal(df)
        signals["run_rate_acceleration"] = self._acceleration_signal(df)

        # Weighted composite — weights MUST sum to 1.0
        momentum = pd.Series(0.0, index=df.index)
        for key, signal in signals.items():
            weight = self.weights.get(key, 0)
            momentum += signal * weight

        # Scale to [-100, +100]
        df["momentum_index"] = (momentum * 100).clip(
            config.MOMENTUM_MIN, config.MOMENTUM_MAX
        ).round(1)

        # Store individual signals for debugging / visualization
        for key, signal in signals.items():
            df[f"signal_{key}"] = signal.round(3)

        return df

    def _run_rate_signal(self, df: pd.DataFrame, innings: int) -> pd.Series:
        """
        Run Rate Factor signal.
        
        1st innings: Based on CRR relative to par rate.
          - CRR = 8.0 → signal = 0 (neutral)
          - CRR = 12.0 → signal = +1 (batting dominant)
          - CRR = 4.0  → signal = -1 (bowling dominant)
          
        2nd innings: Based on CRR vs RRR gap.
          - CRR = RRR → signal = 0 (on track)
          - CRR >> RRR → signal = +1 (batting ahead)
          - CRR << RRR → signal = -1 (bowling ahead)

        Returns:
            Signal in [-1, +1]. Positive = batting ahead.
        """
        crr = df["current_run_rate"].astype(float)

        if innings == 1:
            # T20 par rate is approximately 8.0 runs/over
            par_rate = 8.0
            # Scale: deviation of ±4 from par maps to ±1
            signal = (crr - par_rate) / 4.0
        else:
            rrr = df["required_run_rate"].astype(float)
            # When CRR > RRR, batting is comfortably ahead
            diff = crr - rrr
            # Scale: difference of ±4 runs/over maps to full signal
            signal = diff / 4.0

        return signal.clip(-1, 1)

    def _recent_scoring_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Recent Scoring signal based on runs in last over window (6 balls).

        Calibrated against real T20 statistics:
          - Average T20 over: ~8 runs → signal = 0
          - 0 runs (maiden): signal = -1
          - 16+ runs (explosive): signal = +1

        Formula: signal = (runs_last_over - 8) / 8

        Returns:
            Signal in [-1, +1].
        """
        runs_last_over = df["runs_last_over"].astype(float)
        # Center at 8 (average T20 over), scale by 8
        signal = (runs_last_over - 8.0) / 8.0
        return signal.clip(-1, 1)

    def _wicket_pressure_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Wicket Pressure signal. More recent wickets = bowling dominance.

        Calibrated:
          - 0 wickets in window: signal = 0 (neutral, no bias)
          - 1 wicket: signal = -0.4 (bowling gaining)
          - 2 wickets: signal = -0.8 (strong bowling pressure)
          - 3+ wickets: signal = -1.0 (collapse)

        Formula: signal = -min(wickets * 0.4, 1.0)

        Returns:
            Signal in [-1, 0]. Negative = wickets falling (bowling dominance).
        """
        wickets = df["wickets_last_n"].astype(float)
        # Each wicket contributes -0.4 to the signal, capped at -1.0
        signal = -(wickets * 0.4).clip(upper=1.0)
        return signal.clip(-1, 0)

    def _dot_ball_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Dot Ball Pressure signal. High dot% = bowling dominance.

        Calibrated against T20 averages:
          - 40% dots (average): signal = 0
          - 0% dots (every ball scored): signal = +1
          - 80%+ dots (very tight): signal = -1

        Formula: signal = (40 - dot_pct) / 40

        Returns:
            Signal in [-1, +1]. Negative = high dot ball rate.
        """
        dot_pct = df["dot_ball_pct"].astype(float)
        signal = (40.0 - dot_pct) / 40.0
        return signal.clip(-1, 1)

    def _boundary_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Boundary Frequency signal. More boundaries = batting momentum.

        Calibrated against T20 averages:
          - ~17% boundary rate (average): signal = 0
          - 0% boundaries: signal = -0.85
          - 35%+ boundaries: signal ≈ +1

        Formula: signal = (boundary_freq - 17) / 18

        Returns:
            Signal in [-1, +1]. Positive = hitting boundaries.
        """
        boundary_freq = df["boundary_freq"].astype(float)
        # Center at 17% (T20 average), scale by 18
        signal = (boundary_freq - 17.0) / 18.0
        return signal.clip(-1, 1)

    def _acceleration_signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Run Rate Acceleration signal.
        Positive acceleration = batting gaining momentum.

        Calibrated:
          - Acceleration of 0: signal = 0 (stable rate)
          - Acceleration of +4: signal = +1 (strong acceleration)
          - Acceleration of -4: signal = -1 (sharp deceleration)

        Formula: signal = acceleration / 4

        Returns:
            Signal in [-1, +1].
        """
        accel = df["run_rate_acceleration"].astype(float)
        signal = accel / 4.0
        return signal.clip(-1, 1)
