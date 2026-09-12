"""
Configuration module for Momentum Shift Detector.
All tunable thresholds, weights, and parameters are centralized here.
Modify these values to adjust sensitivity of momentum detection,
win probability calculations, and feature engineering windows.

All values are calibrated against real T20 cricket statistics:
  - Average T20 run rate: ~8.0 runs/over
  - Average T20 score: ~155-165 (20 overs)
  - Average dot ball %: ~40%
  - Average boundary %: ~17%
  - Average wickets per match: ~7-8 per innings
"""

# ─── Match Settings ────────────────────────────────────────────────
TOTAL_OVERS = 20          # Default T20 match length
BALLS_PER_OVER = 6
TOTAL_BALLS = TOTAL_OVERS * BALLS_PER_OVER

# ─── Feature Engineering Windows ───────────────────────────────────
ROLLING_OVER_WINDOW = 6          # Balls in a rolling "last over" window
ROLLING_5_OVER_WINDOW = 30       # Balls for last-5-overs aggregation
WICKET_LOOKBACK_BALLS = 12       # N balls to check for wicket clusters
DOT_BALL_WINDOW = 18             # Window for dot ball percentage (3 overs)
BOUNDARY_WINDOW = 18             # Window for boundary frequency (3 overs)
PRESSURE_WINDOW = 18             # Window for pressure index calculation
RUN_RATE_ACCEL_WINDOW = 12       # Window for run rate acceleration (2 overs)

# ─── Momentum Index Weights ────────────────────────────────────────
# These weights determine how much each feature contributes to the
# Momentum Index. MUST sum to 1.0.
# Positive signal = favours batting, Negative signal = favours bowling.
MOMENTUM_WEIGHTS = {
    "run_rate_factor":       0.25,   # CRR vs RRR/par comparison
    "recent_scoring":        0.20,   # Runs in last over window
    "wicket_pressure":       0.25,   # Wickets in last N balls (highest weight)
    "dot_ball_pressure":     0.12,   # Dot ball percentage
    "boundary_momentum":     0.10,   # Boundary frequency
    "run_rate_acceleration": 0.08,   # Acceleration of scoring rate
}
# Verify weights sum to 1.0
assert abs(sum(MOMENTUM_WEIGHTS.values()) - 1.0) < 0.001, \
    f"Momentum weights must sum to 1.0, got {sum(MOMENTUM_WEIGHTS.values())}"

# ─── Momentum Index Scaling ────────────────────────────────────────
MOMENTUM_MIN = -100   # Full bowling dominance
MOMENTUM_MAX = 100    # Full batting dominance

# ─── Momentum Shift Detection ─────────────────────────────────────
SHIFT_THRESHOLD = 20            # Minimum absolute change to qualify as shift
SHIFT_LOOKBACK_BALLS = 6        # Number of balls over which to measure change
RAPID_SHIFT_THRESHOLD = 35      # Threshold for "rapid" / critical shift
SHIFT_COOLDOWN_BALLS = 6        # Minimum balls between consecutive shift alerts

# ─── Win Probability Parameters ───────────────────────────────────
# Weights for 2nd innings probability model
WIN_PROB_WEIGHTS = {
    "par_score":        0.40,   # Resource-based par score comparison
    "rrr_feasibility":  0.45,   # Required rate achievability
    "momentum":         0.15,   # Current momentum index influence
}

# ─── Pressure Index Thresholds ─────────────────────────────────────
PRESSURE_HIGH_RRR = 10.0     # Required rate considered "high pressure"
PRESSURE_WICKET_WEIGHT = 12  # Points per recent wicket (max 30 total)
PRESSURE_DOT_WEIGHT = 5      # Points per dot ball in window

# ─── Auto-play Speed Settings (milliseconds per ball) ─────────────
AUTOPLAY_SPEED_MIN = 200      # Fastest auto-play (ms)
AUTOPLAY_SPEED_MAX = 3000     # Slowest auto-play (ms)
AUTOPLAY_SPEED_DEFAULT = 1000 # Default speed (ms)

# ─── Dashboard Display Settings ───────────────────────────────────
BALL_FEED_MAX_DISPLAY = 30    # Max balls to show in feed panel
TURNING_POINTS_MAX = 20       # Max turning points to display
