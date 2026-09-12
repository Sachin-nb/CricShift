"""
Run Simulation Pipeline — Phase 3C
====================================
Loads sample data, creates multiple what-if scenarios,
runs simulations, and generates all output artefacts.

Usage:
    python -m models.simulation.run_simulation
"""

import json
import logging
import sys
from pathlib import Path

import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.simulation.simulation_engine import SimulationEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ── Pre-defined what-if scenarios ─────────────────────────────────────────────
SCENARIOS = [
    {
        "name": "Replace batter with a power-hitter",
        "modifications": {
            "replace_batter": "AB de Villiers",
        },
    },
    {
        "name": "Replace bowler with an economical spinner",
        "modifications": {
            "replace_bowler": "R Ashwin",
        },
    },
    {
        "name": "Increase current runs by 20",
        "modifications": {
            "Current_Score": "INCREASE_20",  # Will be handled below
        },
    },
    {
        "name": "Reduce wickets to simulate fewer early collapses",
        "modifications": {
            "Current_Wickets": 1,
        },
    },
    {
        "name": "Move match to death overs with high required rate",
        "modifications": {
            "Current_Over": 17,
            "Current_Ball": 0,
            "Balls_Remaining": 18,
            "Overs_Remaining": 3.0,
            "Death_Overs_Flag": 1,
            "Middle_Overs_Flag": 0,
            "Powerplay_Flag": 0,
        },
    },
    {
        "name": "Change venue to a high-scoring ground",
        "modifications": {
            "Venue": "M Chinnaswamy Stadium",
            "Venue_Run_Rate": 9.5,
            "Venue_Average_Score": 180.0,
        },
    },
    {
        "name": "Swap batting and bowling teams (toss winner change)",
        "modifications": {
            "SWAP_TEAMS": True,
        },
    },
]


def main() -> None:
    logger.info("=" * 60)
    logger.info("  Phase 3C — What-If Simulation Pipeline")
    logger.info("=" * 60)

    output_dir = PROJECT_ROOT / "models" / "simulation"
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. Load engine ───────────────────────────────────────────────────
    engine = SimulationEngine()
    engine.load()

    # ── 2. Load a sample row from the feature dataset ────────────────────
    feature_path = PROJECT_ROOT / "data" / "features" / "feature_dataset.csv"
    logger.info(f"Loading baseline data from {feature_path} …")
    df = pd.read_csv(feature_path, nrows=500)
    # Pick a 2nd-innings row with a meaningful match state
    innings2 = df[df["Innings"].astype(str) == "2"]
    if len(innings2) > 0:
        # Pick a mid-match row
        mid_idx = len(innings2) // 2
        baseline = innings2.iloc[mid_idx]
    else:
        baseline = df.iloc[len(df) // 2]

    logger.info(f"  Baseline: {baseline.get('Batting_Team', 'N/A')} vs "
                 f"{baseline.get('Bowling_Team', 'N/A')} at {baseline.get('Venue', 'N/A')}")
    logger.info(f"  Over {baseline.get('Current_Over', 0)}.{baseline.get('Current_Ball', 0)}, "
                 f"Score: {baseline.get('Current_Score', 0)}/{baseline.get('Current_Wickets', 0)}")

    # ── 3. Process and run each scenario ─────────────────────────────────
    results = []
    comparison_rows = []

    for scenario in SCENARIOS:
        name = scenario["name"]
        mods = scenario["modifications"].copy()

        # Handle special modifications
        if "INCREASE_20" in str(mods.get("Current_Score", "")):
            mods["Current_Score"] = int(baseline.get("Current_Score", 0)) + 20

        if mods.pop("SWAP_TEAMS", False):
            bt = baseline.get("Batting_Team", "")
            bwt = baseline.get("Bowling_Team", "")
            mods["Batting_Team"] = bwt
            mods["Bowling_Team"] = bt

        logger.info(f"\n  Scenario: {name}")
        result = engine.simulate(baseline, mods, scenario_name=name)

        results.append(result)
        comparison_rows.append({
            "Scenario": name,
            "Original_Win_Prob": result["original"]["win_probability_pct"],
            "New_Win_Prob": result["modified"]["win_probability_pct"],
            "Win_Prob_Delta": result["delta"]["win_probability_delta"],
            "Original_Momentum": result["original"]["momentum_label"],
            "New_Momentum": result["modified"]["momentum_label"],
            "Momentum_Delta": result["delta"]["momentum_delta"],
        })
        logger.info(f"    Win: {result['original']['win_probability_pct']}% → "
                     f"{result['modified']['win_probability_pct']}% "
                     f"(Δ {result['delta']['win_probability_delta']:+.2f}pp)")
        logger.info(f"    Momentum: {result['delta']['momentum_shift']}")

    # ── 4. Save sample_simulations.csv ───────────────────────────────────
    comp_df = pd.DataFrame(comparison_rows)
    csv_path = output_dir / "sample_simulations.csv"
    comp_df.to_csv(csv_path, index=False)
    logger.info(f"\n  → Comparison table saved: {csv_path}")

    # ── 5. Save simulation_report.json ───────────────────────────────────
    sim_report = {
        "phase": "3C",
        "module": "What-If Simulation",
        "baseline_context": {
            "batting_team": str(baseline.get("Batting_Team", "")),
            "bowling_team": str(baseline.get("Bowling_Team", "")),
            "venue": str(baseline.get("Venue", "")),
            "over": f"{baseline.get('Current_Over', 0)}.{baseline.get('Current_Ball', 0)}",
            "score": f"{int(baseline.get('Current_Score', 0))}/{int(baseline.get('Current_Wickets', 0))}",
        },
        "scenarios_count": len(results),
        "scenario_results": results,
        "outputs_generated": [
            "simulation_report.json",
            "sample_simulations.csv",
            "comparison_report.json",
        ],
        "status": "SUCCESS",
    }
    report_path = output_dir / "simulation_report.json"
    with open(report_path, "w") as f:
        json.dump(sim_report, f, indent=2, default=str)
    logger.info(f"  → Simulation report saved: {report_path}")

    # ── 6. Save comparison_report.json ───────────────────────────────────
    comparison_report = {
        "phase": "3C",
        "module": "Simulation Comparison",
        "total_scenarios": len(results),
        "comparison_table": comparison_rows,
        "summary": {
            "max_win_prob_increase": max(r["Win_Prob_Delta"] for r in comparison_rows),
            "max_win_prob_decrease": min(r["Win_Prob_Delta"] for r in comparison_rows),
            "scenarios_with_momentum_shift": sum(
                1 for r in comparison_rows if r["Momentum_Delta"] != 0
            ),
        },
        "status": "SUCCESS",
    }
    comp_report_path = output_dir / "comparison_report.json"
    with open(comp_report_path, "w") as f:
        json.dump(comparison_report, f, indent=2, default=str)
    logger.info(f"  → Comparison report saved: {comp_report_path}")

    logger.info("=" * 60)
    logger.info("  Simulation pipeline complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
