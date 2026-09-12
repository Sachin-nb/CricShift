"""
Momentum Shift Detector Module
================================
Detects significant momentum shifts during match progression.
A shift is identified when the Momentum Index changes by more
than a configurable threshold over a rolling window of balls.

Generates descriptive alerts explaining what caused the shift
(e.g., quick wickets, boundary burst, scoring drought).

Features:
  - Configurable shift threshold and lookback window
  - Cooldown period to avoid alert flooding
  - Severity classification (minor / major / critical)
  - Natural language explanations for each detected shift
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


class ShiftDetector:
    """Detect and classify momentum shifts in match data."""

    def __init__(self, threshold: float = None, lookback: int = None,
                 cooldown: int = None):
        """
        Initialize the detector with configurable parameters.

        Args:
            threshold: Minimum momentum change to trigger a shift alert.
            lookback: Number of balls over which to measure the change.
            cooldown: Minimum balls between consecutive alerts.
        """
        self.threshold = threshold or config.SHIFT_THRESHOLD
        self.lookback = lookback or config.SHIFT_LOOKBACK_BALLS
        self.cooldown = cooldown or config.SHIFT_COOLDOWN_BALLS

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect momentum shifts and add shift columns to the DataFrame.

        Args:
            df: DataFrame with 'momentum_index' already computed.

        Returns:
            DataFrame with added columns:
              - 'momentum_change': Rolling change in momentum index
              - 'is_shift': Boolean flag for detected shifts
              - 'shift_severity': 'minor', 'major', or 'critical'
              - 'shift_description': Human-readable explanation
        """
        df = df.copy()

        # Calculate rolling momentum change
        momentum = df["momentum_index"]
        df["momentum_change"] = momentum.diff(periods=self.lookback).fillna(0).round(1)

        # Detect shifts above threshold
        abs_change = df["momentum_change"].abs()
        df["is_shift"] = abs_change >= self.threshold

        # Apply cooldown: suppress shifts that are too close together
        df = self._apply_cooldown(df)

        # Classify severity
        df["shift_severity"] = df.apply(
            lambda row: self._classify_severity(row) if row["is_shift"] else "",
            axis=1
        )

        # Generate descriptions
        df["shift_description"] = df.apply(
            lambda row: self._generate_description(row, df) if row["is_shift"] else "",
            axis=1
        )

        return df

    def _apply_cooldown(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Suppress shift alerts that occur within the cooldown window
        of a previous alert. Keeps the stronger shift if two overlap.
        """
        df = df.copy()
        shift_indices = df[df["is_shift"]].index.tolist()
        suppressed = set()

        for i, idx in enumerate(shift_indices):
            if idx in suppressed:
                continue
            # Suppress subsequent shifts within cooldown
            for j in range(i + 1, len(shift_indices)):
                next_idx = shift_indices[j]
                if (next_idx - idx) <= self.cooldown:
                    # Keep the one with larger absolute change
                    if abs(df.loc[next_idx, "momentum_change"]) > abs(df.loc[idx, "momentum_change"]):
                        suppressed.add(idx)
                        break
                    else:
                        suppressed.add(next_idx)
                else:
                    break

        df.loc[list(suppressed), "is_shift"] = False
        return df

    def _classify_severity(self, row: pd.Series) -> str:
        """
        Classify the severity of a momentum shift.

        Returns:
            'critical', 'major', or 'minor'
        """
        abs_change = abs(row["momentum_change"])
        if abs_change >= config.RAPID_SHIFT_THRESHOLD:
            return "critical"
        elif abs_change >= self.threshold * 1.3:
            return "major"
        else:
            return "minor"

    def _generate_description(self, row: pd.Series, df: pd.DataFrame) -> str:
        """
        Generate a human-readable explanation for a momentum shift.

        Analyzes the context (wickets, boundaries, dots) to explain WHY
        the momentum shifted.
        """
        change = row["momentum_change"]
        direction = "batting" if change > 0 else "bowling"
        abs_change = abs(change)

        # Look at contributing factors
        explanations = []

        # Check for wickets
        wickets = row.get("wickets_last_n", 0)
        if wickets >= 2 and change < 0:
            explanations.append(f"{int(wickets)} wickets in quick succession")
        elif wickets >= 1 and change < 0:
            explanations.append("key wicket falls")

        # Check for boundary burst
        boundary_freq = row.get("boundary_freq", 0)
        if boundary_freq > 30 and change > 0:
            explanations.append("boundary blitz")
        elif boundary_freq > 20 and change > 0:
            explanations.append("frequent boundary hitting")

        # Check for scoring acceleration
        accel = row.get("run_rate_acceleration", 0)
        if accel > 2 and change > 0:
            explanations.append("sharp scoring acceleration")
        elif accel < -2 and change < 0:
            explanations.append("significant scoring slow-down")

        # Check for dot ball pressure
        dot_pct = row.get("dot_ball_pct", 0)
        if dot_pct > 60 and change < 0:
            explanations.append("sustained dot ball pressure")
        elif dot_pct < 25 and change > 0:
            explanations.append("consistent run scoring")

        # Check runs in last over
        runs_last = row.get("runs_last_over", 0)
        if runs_last >= 15 and change > 0:
            explanations.append(f"explosive over ({int(runs_last)} runs)")
        elif runs_last <= 2 and change < 0:
            explanations.append(f"maiden-like over ({int(runs_last)} runs)")

        # Build description
        over_ball = f"{int(row.get('over', 0))}.{int(row.get('ball', 0))}"
        severity = self._classify_severity(row)
        severity_label = severity.upper()

        if explanations:
            reason = ", ".join(explanations)
        else:
            reason = f"{'aggressive batting' if change > 0 else 'tight bowling'}"

        description = (
            f"[{severity_label}] Momentum shifts towards {direction} "
            f"(Δ{'+' if change > 0 else ''}{change:.0f}) at over {over_ball}: "
            f"{reason}"
        )

        return description

    def get_turning_points(self, df: pd.DataFrame) -> list:
        """
        Extract all detected turning points as a list of dictionaries.

        Args:
            df: DataFrame with shift detection already applied.

        Returns:
            List of turning point dictionaries with metadata.
        """
        shifts = df[df["is_shift"]].copy()
        turning_points = []

        for _, row in shifts.iterrows():
            turning_points.append({
                "ball_number": int(row.get("ball_number", 0)),
                "over": f"{int(row.get('over', 0))}.{int(row.get('ball', 0))}",
                "momentum_before": round(row["momentum_index"] - row["momentum_change"], 1),
                "momentum_after": round(row["momentum_index"], 1),
                "change": round(row["momentum_change"], 1),
                "severity": row["shift_severity"],
                "description": row["shift_description"],
                "batting_team": row.get("batting_team", ""),
                "bowling_team": row.get("bowling_team", ""),
                "score": f"{int(row.get('cumulative_runs', 0))}/{int(row.get('cumulative_wickets', 0))}",
            })

        return turning_points[:config.TURNING_POINTS_MAX]
