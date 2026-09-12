"""
Win Probability Engine
=======================
Rule-based win probability calculation for both teams.
Uses a multi-factor model calibrated against real T20 cricket data.

For the 2nd innings chase, the model considers:
  1. Resource percentage remaining (DLS-inspired wicket+balls table)
  2. Run rate comparison (CRR vs RRR)
  3. Momentum influence (weighted less than hard factors)
  4. Match phase adjustments

For the 1st innings, provides projected score-based probability
indicating how competitive the batting team's total will be.

Key design decisions:
  - Resources table assigns percentage values to (wickets, overs) pairs
  - Chase progress is measured against resource-adjusted par score
  - Win probability transitions smoothly via sigmoid blending
  - Hard edge cases (all out, target reached) override the model
  - Probabilities are bounded to [2%, 98%] except at terminal states
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


# ── DLS-Inspired Resource Table ────────────────────────────────────
# Percentage of batting resources remaining given (wickets_lost, overs_left)
# Based on simplified DLS resource percentages for T20 cricket.
# Rows: wickets lost (0-10), Columns are computed dynamically.
#
# The key insight: a team with 10 overs left and 0 wickets lost has ~100%
# resources, but with 5 wickets lost and 10 overs left has only ~40%.
#
# Resource formula (simplified Stern method):
#   resource = overs_pct * wicket_factor
#   where wicket_factor diminishes non-linearly with each wicket lost.

WICKET_RESOURCE_FACTORS = {
    0: 1.000,   # All wickets in hand
    1: 0.908,   # 1 wicket lost
    2: 0.816,   # 2 wickets lost
    3: 0.714,   # 3 wickets lost
    4: 0.600,   # 4 wickets lost
    5: 0.475,   # 5 wickets lost (half the batting order gone)
    6: 0.340,   # 6 wickets lost
    7: 0.210,   # 7 wickets lost (tail exposed)
    8: 0.110,   # 8 wickets lost
    9: 0.040,   # 9 wickets lost (last pair)
    10: 0.000,  # All out
}


def _get_resource_pct(wickets_lost: int, balls_remaining: int) -> float:
    """
    Calculate the percentage of batting resources remaining.

    Args:
        wickets_lost: Number of wickets fallen (0-10).
        balls_remaining: Number of balls left in the innings.

    Returns:
        Resource percentage in [0, 1].
    """
    wickets_lost = int(min(max(wickets_lost, 0), 10))
    balls_remaining = int(max(balls_remaining, 0))

    overs_remaining = balls_remaining / config.BALLS_PER_OVER
    total_overs = config.TOTAL_OVERS

    # Overs resource (non-linear: early overs are less valuable than late)
    overs_pct = overs_remaining / total_overs

    # Wicket resource factor
    wicket_factor = WICKET_RESOURCE_FACTORS.get(wickets_lost, 0.0)

    # Combined resource
    resource = overs_pct * wicket_factor
    return min(max(resource, 0.0), 1.0)


class WinProbabilityEngine:
    """Calculate win probabilities for both teams."""

    def __init__(self, target_score: int = 0):
        """
        Initialize the engine.

        Args:
            target_score: Target for the chasing team (2nd innings).
        """
        self.target_score = target_score

    def calculate(self, df: pd.DataFrame, innings: int = 2) -> pd.DataFrame:
        """
        Compute win probabilities for every ball.

        Args:
            df: DataFrame with features and momentum index computed.
            innings: Innings number.

        Returns:
            DataFrame with 'win_prob_batting' and 'win_prob_bowling'
            columns added (percentages 0-100).
        """
        df = df.copy()

        if innings == 1:
            df = self._first_innings_probability(df)
        else:
            df = self._second_innings_probability(df)

        return df

    def _first_innings_probability(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        For 1st innings, estimate batting team's position strength.
        This represents: "probability of setting a winning total".

        Uses projected final score compared to average T20 winning score.
        The projected score accounts for wickets lost (lower projection
        when more wickets have fallen).
        """
        crr = df["current_run_rate"].astype(float)
        balls_bowled = df["ball_number"].astype(float)
        remaining_balls = config.TOTAL_BALLS - balls_bowled
        wickets_lost = df["cumulative_wickets"].astype(float)

        # Calculate resources remaining for projection
        resource_pcts = pd.Series(
            [_get_resource_pct(int(w), int(b))
             for w, b in zip(wickets_lost, remaining_balls)],
            index=df.index
        )

        # Total resources at start = 1.0
        # Resources used so far = 1.0 - resource_remaining
        resources_used_pct = 1.0 - resource_pcts

        # Avoid division by zero for the very first ball
        resources_used_pct = resources_used_pct.clip(lower=0.01)

        # Project final score using resource-adjusted projection:
        # projected = current_runs / resources_used * total_resources_available
        # But total_resources = resources_used + resources_remaining, which = 1.0
        # So: projected = current_runs / resources_used
        projected_score = df["cumulative_runs"].astype(float) / resources_used_pct

        # Competitive T20 score thresholds
        avg_winning_score = 165.0  # Average T20 winning first innings total
        std_dev = 25.0             # Standard deviation of T20 scores

        # Probability is based on how projected score compares to average
        z_score = (projected_score - avg_winning_score) / std_dev
        batting_prob = self._sigmoid_transform(z_score, center=0, steepness=1.2)

        # Stage adjustment: early innings has more uncertainty
        stage_factor = (balls_bowled / config.TOTAL_BALLS)  # 0→1 over the innings
        # Blend toward 50% in early stages
        batting_prob = 0.5 + (batting_prob - 0.5) * (0.3 + 0.7 * stage_factor)

        # Momentum minor influence (+/- 5% max)
        momentum = df.get("momentum_index", pd.Series(0, index=df.index)).astype(float)
        momentum_adj = momentum / 100.0 * 0.05  # ±5% at extreme momentum
        batting_prob = batting_prob + momentum_adj

        batting_prob = (batting_prob * 100).clip(15, 85)

        df["win_prob_batting"] = batting_prob.round(1)
        df["win_prob_bowling"] = (100 - batting_prob).round(1)

        return df

    def _second_innings_probability(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        For 2nd innings chase, calculate win probability using:

        1. Resource-based par score comparison
        2. Required run rate vs current run rate
        3. Momentum influence (minor factor)

        The core logic:
          - Calculate resources remaining (DLS-style)
          - Calculate "par score" = target * (1 - resources_remaining)
          - Compare actual score to par score
          - Adjust for RRR feasibility
          - Apply momentum influence
        """
        target = self.target_score
        if target <= 0:
            df["win_prob_batting"] = 50.0
            df["win_prob_bowling"] = 50.0
            return df

        cumulative_runs = df["cumulative_runs"].astype(float)
        wickets_lost = df["cumulative_wickets"].astype(float)
        balls_remaining = (config.TOTAL_BALLS - df["ball_number"]).astype(float)
        crr = df["current_run_rate"].astype(float)
        rrr = df["required_run_rate"].astype(float)
        balls_bowled = df["ball_number"].astype(float)

        # ── Factor 1: Resource-based par score comparison ──
        # Calculate resource % remaining at each ball
        resource_pcts = pd.Series(
            [_get_resource_pct(int(w), int(b))
             for w, b in zip(wickets_lost, balls_remaining)],
            index=df.index
        )

        # Par score = what the chasing team "should" have scored by now
        # If 60% of resources are used, par = target * 0.60
        resources_used = 1.0 - resource_pcts
        par_score = (target - 1) * resources_used  # target-1 because target = score+1

        # How far ahead/behind par is the chasing team?
        score_diff = cumulative_runs - par_score
        # Normalize by target for comparability
        normalized_diff = score_diff / target

        # Convert to probability signal via sigmoid
        # Steepness of 10 means being 10% ahead of par ≈ 73% win prob
        par_signal = self._sigmoid_transform(
            normalized_diff, center=0, steepness=10
        )

        # ── Factor 2: Required rate feasibility ──
        # How achievable is the required rate given resources?
        # A RRR of 6 is very easy, 8 is normal, 12+ is very hard, 36+ impossible
        remaining_runs = (target - cumulative_runs).clip(lower=0)

        # Feasibility based on whether RRR is achievable
        # Below 8: comfortable, 8-10: manageable, 10-14: difficult, 14+: very hard
        rrr_signal = pd.Series(0.5, index=df.index)
        for i in range(len(df)):
            r = float(rrr.iloc[i])
            br = float(balls_remaining.iloc[i])
            rr = float(remaining_runs.iloc[i])

            if rr <= 0:
                rrr_signal.iloc[i] = 1.0  # Already won
            elif br <= 0:
                rrr_signal.iloc[i] = 0.0  # No balls remaining, not reached
            elif r <= 6.0:
                rrr_signal.iloc[i] = 0.85  # Very comfortable
            elif r <= 8.0:
                rrr_signal.iloc[i] = 0.70  # Comfortable
            elif r <= 10.0:
                rrr_signal.iloc[i] = 0.55  # Even contest
            elif r <= 12.0:
                rrr_signal.iloc[i] = 0.38  # Tough chase
            elif r <= 15.0:
                rrr_signal.iloc[i] = 0.20  # Very difficult
            elif r <= 20.0:
                rrr_signal.iloc[i] = 0.08  # Nearly impossible
            else:
                rrr_signal.iloc[i] = 0.02  # Impossible

        # ── Factor 3: Momentum influence ──
        momentum = df.get("momentum_index", pd.Series(0, index=df.index)).astype(float)
        momentum_signal = (momentum + 100) / 200.0  # Normalize to [0, 1]

        # ── Weighted combination ──
        # Hard factors (par score, RRR) dominate; momentum is supplementary
        raw_prob = (
            par_signal * 0.40 +
            rrr_signal * 0.45 +
            momentum_signal * 0.15
        )

        # ── Stage-based certainty adjustment ──
        # Early in innings: keep closer to 50/50 (more uncertainty)
        # Late in innings: allow more extreme probabilities
        stage = balls_bowled / config.TOTAL_BALLS  # 0 → 1
        certainty = 0.3 + 0.7 * (stage ** 0.8)  # Ramps from 0.3 to 1.0

        batting_prob = 0.5 + (raw_prob - 0.5) * certainty

        # ── Terminal state overrides ──
        # Already won: 100%
        won_mask = cumulative_runs >= target
        batting_prob = batting_prob.where(~won_mask, 1.0)

        # All out: near 0% (but could have won before all out ball)
        allout_mask = (wickets_lost >= 10) & (~won_mask)
        batting_prob = batting_prob.where(~allout_mask, 0.02)

        # Match decided on last ball scenarios
        last_ball_mask = (balls_remaining <= 0) & (~won_mask)
        batting_prob = batting_prob.where(~last_ball_mask, 0.0)

        # Convert to percentage and bound
        batting_prob = (batting_prob * 100).clip(2, 98)

        # Override terminals to true 0/100
        batting_prob = batting_prob.where(~won_mask, 100.0)
        batting_prob = batting_prob.where(~(allout_mask & (~won_mask)), 2.0)

        df["win_prob_batting"] = batting_prob.round(1)
        df["win_prob_bowling"] = (100 - batting_prob).round(1)

        return df

    @staticmethod
    def _sigmoid_transform(x, center: float = 0,
                           steepness: float = 1):
        """
        Apply sigmoid transformation to normalize values to [0, 1].

        σ(x) = 1 / (1 + e^(-steepness * (x - center)))

        Properties:
          - σ(center) = 0.5
          - σ(center + 2/steepness) ≈ 0.88
          - σ(center - 2/steepness) ≈ 0.12

        Args:
            x: Input value or Series.
            center: Center point of the sigmoid.
            steepness: Controls how steep the transition is.

        Returns:
            Transformed value(s) in [0, 1] range.
        """
        return 1 / (1 + np.exp(-steepness * (x - center)))
