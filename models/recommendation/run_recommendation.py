"""
Run Recommendation Pipeline — Phase 3C
========================================
Creates sample match scenarios, runs the RecommendationEngine,
and generates player_rankings.csv + recommendation_report.json.

Usage:
    python -m models.recommendation.run_recommendation
"""

import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.recommendation.recommendation_engine import (
    RecommendationEngine,
    default_match_situation,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


SAMPLE_SCENARIOS = [
    {
        "name": "High-pressure death-over chase",
        "situation": {
            "batting_team": "Mumbai Indians",
            "bowling_team": "Chennai Super Kings",
            "venue": "Wankhede Stadium",
            "current_score": 140,
            "current_wickets": 5,
            "current_over": 16,
            "required_run_rate": 12.5,
            "pressure_index": 72.0,
            "momentum_score": -15.0,
            "current_batter": "Rohit Sharma",
            "current_bowler": "DJ Bravo",
            "dismissed_batters": ["SA Yadav", "Ishan Kishan", "T David"],
        },
    },
    {
        "name": "Powerplay rebuilding after early wickets",
        "situation": {
            "batting_team": "Royal Challengers Bangalore",
            "bowling_team": "Rajasthan Royals",
            "venue": "M Chinnaswamy Stadium",
            "current_score": 22,
            "current_wickets": 3,
            "current_over": 4,
            "required_run_rate": 0.0,
            "pressure_index": 45.0,
            "momentum_score": -30.0,
            "current_batter": "V Kohli",
            "current_bowler": "YS Chahal",
            "dismissed_batters": ["Faf du Plessis", "GJ Maxwell"],
        },
    },
    {
        "name": "Comfortable middle-overs consolidation",
        "situation": {
            "batting_team": "Kolkata Knight Riders",
            "bowling_team": "Punjab Kings",
            "venue": "Eden Gardens",
            "current_score": 85,
            "current_wickets": 1,
            "current_over": 10,
            "required_run_rate": 7.0,
            "pressure_index": 15.0,
            "momentum_score": 25.0,
            "current_batter": "N Rana",
            "current_bowler": "Arshdeep Singh",
            "dismissed_batters": [],
        },
    },
]


def main() -> None:
    logger.info("=" * 60)
    logger.info("  Phase 3C — Recommendation Pipeline")
    logger.info("=" * 60)

    output_dir = PROJECT_ROOT / "models" / "recommendation"
    output_dir.mkdir(parents=True, exist_ok=True)

    engine = RecommendationEngine()
    engine.load_data()

    # ── 1. Generate global player rankings ───────────────────────────────
    rankings = engine.generate_rankings(output_dir)
    logger.info(f"  Top 5 players:\n{rankings.head().to_string(index=False)}")

    # ── 2. Run sample scenarios ──────────────────────────────────────────
    scenario_results = []
    for scenario in SAMPLE_SCENARIOS:
        logger.info(f"\n  Scenario: {scenario['name']}")
        recs = engine.recommend(scenario["situation"], top_n=5)
        for i, rec in enumerate(recs, 1):
            logger.info(f"    #{i} {rec['Player']} — Score: {rec['Recommendation_Score']:.1f}  "
                         f"Confidence: {rec['Confidence']:.2f}")

        scenario_results.append({
            "scenario_name": scenario["name"],
            "match_situation": scenario["situation"],
            "recommendations": recs,
        })

    # ── 3. Build report ──────────────────────────────────────────────────
    report = {
        "phase": "3C",
        "module": "Recommendation Engine",
        "total_players_ranked": len(rankings),
        "scenarios_tested": len(scenario_results),
        "scenario_results": scenario_results,
        "scoring_weights": RecommendationEngine.WEIGHTS,
        "rules_enforced": [
            "Never recommend players from the bowling team",
            "Only recommend available (non-dismissed) batters",
            "Players with < 5 matches get lower confidence",
            "Recommendations ranked by composite score",
        ],
        "outputs_generated": [
            "player_rankings.csv",
            "recommendation_report.json",
        ],
        "status": "SUCCESS",
    }

    report_path = output_dir / "recommendation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"\n  → Report saved: {report_path}")

    logger.info("=" * 60)
    logger.info("  Recommendation pipeline complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
