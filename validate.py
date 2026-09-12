"""
Validation Script
==================
Verifies that all calculations produce mathematically correct results
with known test cases. Run this to validate the analytics engine.
"""
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np

from engine.data_loader import DataLoader
from engine.feature_engine import FeatureEngine
from engine.momentum_model import MomentumModel
from engine.win_probability import WinProbabilityEngine
from engine.shift_detector import ShiftDetector
import config

PASS = "[PASS]"
FAIL = "[FAIL]"
errors = []

def check(name, condition, detail=""):
    if condition:
        print(f"  {PASS} {name}")
    else:
        msg = f"  {FAIL} {name}" + (f" — {detail}" if detail else "")
        print(msg)
        errors.append(msg)

print("=" * 60)
print("ANALYTICS ENGINE VALIDATION")
print("=" * 60)

# ── Load sample data ───────────────────────────────────────────
print("\n1. DATA LOADING")
loader = DataLoader(os.path.join("data", "sample_match.csv"))
df = loader.load()
teams = loader.get_teams()
summary = loader.get_match_summary()

check("CSV loads without error", df is not None)
check("Has both innings", df["innings"].nunique() == 2)
check("Teams extracted", len(teams["team1"]) > 0 and len(teams["team2"]) > 0,
      f"{teams['team1']} vs {teams['team2']}")
check("Ball numbers start at 1", df.groupby("innings")["ball_number"].first().min() == 1)
check("Cumulative runs are monotonic per innings",
      all(df.groupby("innings")["cumulative_runs"].apply(lambda x: x.is_monotonic_increasing)))
check("Cumulative wickets are monotonic per innings",
      all(df.groupby("innings")["cumulative_wickets"].apply(lambda x: x.is_monotonic_increasing)))

# ── Feature Engine Validation ──────────────────────────────────
print("\n2. FEATURE ENGINE")
inn1 = loader.get_innings_data(1)
inn2 = loader.get_innings_data(2)
target = int(inn1["total_runs"].sum()) + 1

fe = FeatureEngine(target_score=target)

# Test innings 1
df1 = fe.compute_features(inn1, innings=1)
check("CRR is always >= 0", (df1["current_run_rate"] >= 0).all())
check("RRR is 0 for innings 1", (df1["required_run_rate"] == 0).all())
check("Dot ball % is in [0, 100]",
      (df1["dot_ball_pct"] >= 0).all() and (df1["dot_ball_pct"] <= 100).all())
check("Boundary freq is in [0, 100]",
      (df1["boundary_freq"] >= 0).all() and (df1["boundary_freq"] <= 100).all())
check("Pressure index is in [0, 100]",
      (df1["pressure_index"] >= 0).all() and (df1["pressure_index"] <= 100).all())

# Manually verify CRR for first ball
first_ball = df1.iloc[0]
expected_crr = first_ball["cumulative_runs"] / (1.0 / 6.0)
check("CRR first ball is correct",
      abs(first_ball["current_run_rate"] - round(expected_crr, 2)) < 0.1,
      f"got {first_ball['current_run_rate']}, expected {round(expected_crr, 2)}")

# Manually verify CRR for ball 12
if len(df1) > 12:
    ball_12 = df1.iloc[11]
    expected_crr12 = ball_12["cumulative_runs"] / (12.0 / 6.0)
    check("CRR at ball 12 is correct",
          abs(ball_12["current_run_rate"] - round(expected_crr12, 2)) < 0.1,
          f"got {ball_12['current_run_rate']}, expected {round(expected_crr12, 2)}")

# Test innings 2
df2 = fe.compute_features(inn2, innings=2)
check("RRR is >= 0 for innings 2", (df2["required_run_rate"] >= 0).all())
check("No NaN in CRR", df2["current_run_rate"].notna().all())
check("No NaN in RRR", df2["required_run_rate"].notna().all())
check("No NaN in pressure index", df2["pressure_index"].notna().all())

# Manually verify RRR for first ball of innings 2
first_ball2 = df2.iloc[0]
remaining_runs = target - first_ball2["cumulative_runs"]
remaining_balls = config.TOTAL_BALLS - 1
remaining_overs = remaining_balls / 6.0
expected_rrr = remaining_runs / remaining_overs if remaining_overs > 0 else 0
check("RRR first ball innings 2 is correct",
      abs(first_ball2["required_run_rate"] - round(expected_rrr, 2)) < 0.1,
      f"got {first_ball2['required_run_rate']}, expected {round(expected_rrr, 2)}")

# Verify runs_last_over sums correctly
if len(df1) >= 6:
    ball_6 = df1.iloc[5]
    manual_sum = df1.iloc[0:6]["total_runs"].sum()
    check("Runs last over at ball 6 = sum of first 6 balls",
          abs(ball_6["runs_last_over"] - manual_sum) < 0.01,
          f"got {ball_6['runs_last_over']}, expected {manual_sum}")

# ── Momentum Model Validation ─────────────────────────────────
print("\n3. MOMENTUM MODEL")
mm = MomentumModel()
df1_m = mm.calculate(df1, innings=1)
df2_m = mm.calculate(df2, innings=2)

check("Momentum index is in [-100, 100]",
      (df1_m["momentum_index"] >= -100).all() and (df1_m["momentum_index"] <= 100).all())
check("No NaN in momentum index", df1_m["momentum_index"].notna().all())
check("Inn2 momentum in range",
      (df2_m["momentum_index"] >= -100).all() and (df2_m["momentum_index"] <= 100).all())

# Verify signal ranges
for sig_name in ["run_rate_factor", "recent_scoring", "wicket_pressure",
                 "dot_ball_pressure", "boundary_momentum", "run_rate_acceleration"]:
    col = f"signal_{sig_name}"
    if col in df1_m.columns:
        check(f"Signal {sig_name} in [-1, +1]",
              (df1_m[col] >= -1.001).all() and (df1_m[col] <= 1.001).all(),
              f"range [{df1_m[col].min():.3f}, {df1_m[col].max():.3f}]")

# Verify weights sum to 1.0
weight_sum = sum(config.MOMENTUM_WEIGHTS.values())
check("Momentum weights sum to 1.0", abs(weight_sum - 1.0) < 0.001,
      f"got {weight_sum}")

# ── Win Probability Validation ─────────────────────────────────
print("\n4. WIN PROBABILITY")
wp1 = WinProbabilityEngine(target_score=0)
df1_wp = wp1.calculate(df1_m, innings=1)

check("Inn1 batting prob in [0, 100]",
      (df1_wp["win_prob_batting"] >= 0).all() and (df1_wp["win_prob_batting"] <= 100).all())
check("Inn1 probs sum to 100",
      ((df1_wp["win_prob_batting"] + df1_wp["win_prob_bowling"]) - 100).abs().max() < 0.2)

wp2 = WinProbabilityEngine(target_score=target)
df2_wp = wp2.calculate(df2_m, innings=2)

check("Inn2 batting prob in [0, 100]",
      (df2_wp["win_prob_batting"] >= 0).all() and (df2_wp["win_prob_batting"] <= 100).all())
check("Inn2 probs sum to 100",
      ((df2_wp["win_prob_batting"] + df2_wp["win_prob_bowling"]) - 100).abs().max() < 0.2)
check("No NaN in win prob batting", df2_wp["win_prob_batting"].notna().all())
check("No NaN in win prob bowling", df2_wp["win_prob_bowling"].notna().all())

# Check if target reached, probability should be 100
if (df2_wp["cumulative_runs"] >= target).any():
    won_rows = df2_wp[df2_wp["cumulative_runs"] >= target]
    check("Win prob = 100 when target reached",
          (won_rows["win_prob_batting"] == 100.0).all(),
          f"got {won_rows['win_prob_batting'].unique()}")

# ── Shift Detector Validation ──────────────────────────────────
print("\n5. SHIFT DETECTION")
sd = ShiftDetector()
df2_sd = sd.detect(df2_wp)

check("momentum_change column exists", "momentum_change" in df2_sd.columns)
check("is_shift column exists", "is_shift" in df2_sd.columns)
check("No NaN in momentum_change", df2_sd["momentum_change"].notna().all())

turning_points = sd.get_turning_points(df2_sd)
check("Turning points is a list", isinstance(turning_points, list))

if turning_points:
    tp = turning_points[0]
    check("Turning point has required keys",
          all(k in tp for k in ["ball_number", "over", "severity", "description"]))
    check("Severity is valid",
          all(tp["severity"] in ["minor", "major", "critical"] for tp in turning_points))

# Verify cooldown: no two shifts within cooldown window
if len(turning_points) >= 2:
    for i in range(1, len(turning_points)):
        gap = turning_points[i]["ball_number"] - turning_points[i-1]["ball_number"]
        check(f"Cooldown respected (gap={gap} >= {config.SHIFT_COOLDOWN_BALLS})",
              gap >= config.SHIFT_COOLDOWN_BALLS,
              f"TP at ball {turning_points[i-1]['ball_number']} and {turning_points[i]['ball_number']}")

# ── Summary ────────────────────────────────────────────────────
print("\n" + "=" * 60)
if errors:
    print(f"VALIDATION COMPLETE: {len(errors)} FAILURES")
    for e in errors:
        print(e)
else:
    print("VALIDATION COMPLETE: ALL CHECKS PASSED  ✓")
print("=" * 60)
