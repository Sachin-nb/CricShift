"""
Phase 3C Validation Script
============================
Verifies integrity of all Phase 3C outputs:
  • No missing values in generated CSVs
  • No invalid recommendations
  • No impossible simulations
  • No incompatible player selections
  • All JSON reports are well-formed

Generates: models/explainability/validation_report.json
           (shared across all Phase 3C modules)

Usage:
    python -m models.validate_phase3c
"""

import json
import logging
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

EXPLAINABILITY_DIR = PROJECT_ROOT / "models" / "explainability"
RECOMMENDATION_DIR = PROJECT_ROOT / "models" / "recommendation"
SIMULATION_DIR = PROJECT_ROOT / "models" / "simulation"


def validate_explainability() -> dict:
    """Validate all explainability outputs."""
    checks = []
    status = "PASS"

    # 1. global_feature_importance.csv
    csv_path = EXPLAINABILITY_DIR / "global_feature_importance.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        missing = int(df.isnull().sum().sum())
        checks.append({"file": "global_feature_importance.csv", "exists": True,
                        "rows": len(df), "missing_values": missing,
                        "pass": missing == 0})
        if missing > 0:
            status = "FAIL"
    else:
        checks.append({"file": "global_feature_importance.csv", "exists": False, "pass": False})
        status = "FAIL"

    # 2. shap_summary.png
    png_path = EXPLAINABILITY_DIR / "shap_summary.png"
    exists = png_path.exists()
    size = png_path.stat().st_size if exists else 0
    checks.append({"file": "shap_summary.png", "exists": exists,
                    "size_bytes": size, "pass": exists and size > 0})
    if not exists or size == 0:
        status = "FAIL"

    # 3. sample_local_explanations.json
    json_path = EXPLAINABILITY_DIR / "sample_local_explanations.json"
    if json_path.exists():
        try:
            with open(json_path) as f:
                data = json.load(f)
            valid = isinstance(data, list) and len(data) > 0
            # Check each sample has required keys
            required_keys = {"momentum_prediction", "win_prediction", "match_context"}
            all_valid = all(required_keys.issubset(set(d.keys())) for d in data)
            checks.append({"file": "sample_local_explanations.json", "exists": True,
                            "samples": len(data), "valid_structure": all_valid,
                            "pass": valid and all_valid})
            if not (valid and all_valid):
                status = "FAIL"
        except json.JSONDecodeError:
            checks.append({"file": "sample_local_explanations.json", "exists": True,
                            "pass": False, "error": "Invalid JSON"})
            status = "FAIL"
    else:
        checks.append({"file": "sample_local_explanations.json", "exists": False, "pass": False})
        status = "FAIL"

    # 4. explainability_report.json
    report_path = EXPLAINABILITY_DIR / "explainability_report.json"
    if report_path.exists():
        try:
            with open(report_path) as f:
                report = json.load(f)
            valid = report.get("status") == "SUCCESS"
            checks.append({"file": "explainability_report.json", "exists": True,
                            "status": report.get("status"), "pass": valid})
            if not valid:
                status = "FAIL"
        except json.JSONDecodeError:
            checks.append({"file": "explainability_report.json", "exists": True,
                            "pass": False, "error": "Invalid JSON"})
            status = "FAIL"
    else:
        checks.append({"file": "explainability_report.json", "exists": False, "pass": False})
        status = "FAIL"

    return {"module": "Explainability", "status": status, "checks": checks}


def validate_recommendation() -> dict:
    """Validate all recommendation outputs."""
    checks = []
    status = "PASS"

    # 1. player_rankings.csv
    csv_path = RECOMMENDATION_DIR / "player_rankings.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        missing = int(df.isnull().sum().sum())
        has_scores = "Ranking_Score" in df.columns
        all_positive = (df["Ranking_Score"] >= 0).all() if has_scores else False
        no_duplicates = not df["Player_Name"].duplicated().any() if "Player_Name" in df.columns else False
        checks.append({"file": "player_rankings.csv", "exists": True,
                        "rows": len(df), "missing_values": missing,
                        "scores_valid": bool(all_positive),
                        "no_duplicate_players": bool(no_duplicates),
                        "pass": missing == 0 and all_positive and no_duplicates})
        if missing > 0 or not all_positive or not no_duplicates:
            status = "FAIL"
    else:
        checks.append({"file": "player_rankings.csv", "exists": False, "pass": False})
        status = "FAIL"

    # 2. recommendation_report.json
    report_path = RECOMMENDATION_DIR / "recommendation_report.json"
    if report_path.exists():
        try:
            with open(report_path) as f:
                report = json.load(f)
            valid_status = report.get("status") == "SUCCESS"

            # Validate recommendations: no invalid entries
            invalid_recs = 0
            for scenario in report.get("scenario_results", []):
                for rec in scenario.get("recommendations", []):
                    if not rec.get("Player"):
                        invalid_recs += 1
                    if rec.get("Recommendation_Score", -1) < 0:
                        invalid_recs += 1
                    if rec.get("Confidence", -1) < 0 or rec.get("Confidence", 2) > 1:
                        invalid_recs += 1

            checks.append({"file": "recommendation_report.json", "exists": True,
                            "status": report.get("status"),
                            "scenarios": report.get("scenarios_tested", 0),
                            "invalid_recommendations": invalid_recs,
                            "pass": valid_status and invalid_recs == 0})
            if not valid_status or invalid_recs > 0:
                status = "FAIL"
        except json.JSONDecodeError:
            checks.append({"file": "recommendation_report.json", "exists": True,
                            "pass": False, "error": "Invalid JSON"})
            status = "FAIL"
    else:
        checks.append({"file": "recommendation_report.json", "exists": False, "pass": False})
        status = "FAIL"

    return {"module": "Recommendation", "status": status, "checks": checks}


def validate_simulation() -> dict:
    """Validate all simulation outputs."""
    checks = []
    status = "PASS"

    # 1. sample_simulations.csv
    csv_path = SIMULATION_DIR / "sample_simulations.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        missing = int(df.isnull().sum().sum())
        # Check win probabilities are in valid range
        probs_valid = True
        for col in ["Original_Win_Prob", "New_Win_Prob"]:
            if col in df.columns:
                if (df[col] < 0).any() or (df[col] > 100).any():
                    probs_valid = False
        checks.append({"file": "sample_simulations.csv", "exists": True,
                        "rows": len(df), "missing_values": missing,
                        "probabilities_valid": probs_valid,
                        "pass": missing == 0 and probs_valid})
        if missing > 0 or not probs_valid:
            status = "FAIL"
    else:
        checks.append({"file": "sample_simulations.csv", "exists": False, "pass": False})
        status = "FAIL"

    # 2. simulation_report.json
    report_path = SIMULATION_DIR / "simulation_report.json"
    if report_path.exists():
        try:
            with open(report_path) as f:
                report = json.load(f)
            valid = report.get("status") == "SUCCESS"

            # Check for impossible simulations
            impossible = 0
            for result in report.get("scenario_results", []):
                orig_wp = result.get("original", {}).get("win_probability_pct", -1)
                new_wp = result.get("modified", {}).get("win_probability_pct", -1)
                if orig_wp < 0 or orig_wp > 100 or new_wp < 0 or new_wp > 100:
                    impossible += 1

            checks.append({"file": "simulation_report.json", "exists": True,
                            "status": report.get("status"),
                            "scenarios": report.get("scenarios_count", 0),
                            "impossible_simulations": impossible,
                            "pass": valid and impossible == 0})
            if not valid or impossible > 0:
                status = "FAIL"
        except json.JSONDecodeError:
            checks.append({"file": "simulation_report.json", "exists": True,
                            "pass": False, "error": "Invalid JSON"})
            status = "FAIL"
    else:
        checks.append({"file": "simulation_report.json", "exists": False, "pass": False})
        status = "FAIL"

    # 3. comparison_report.json
    comp_path = SIMULATION_DIR / "comparison_report.json"
    if comp_path.exists():
        try:
            with open(comp_path) as f:
                comp = json.load(f)
            valid = comp.get("status") == "SUCCESS"
            checks.append({"file": "comparison_report.json", "exists": True,
                            "status": comp.get("status"),
                            "pass": valid})
            if not valid:
                status = "FAIL"
        except json.JSONDecodeError:
            checks.append({"file": "comparison_report.json", "exists": True,
                            "pass": False, "error": "Invalid JSON"})
            status = "FAIL"
    else:
        checks.append({"file": "comparison_report.json", "exists": False, "pass": False})
        status = "FAIL"

    return {"module": "Simulation", "status": status, "checks": checks}


def main() -> None:
    logger.info("=" * 60)
    logger.info("  Phase 3C — Validation")
    logger.info("=" * 60)

    results = {
        "phase": "3C",
        "validation": "Comprehensive",
        "modules": [],
    }

    # Validate each module
    exp_result = validate_explainability()
    rec_result = validate_recommendation()
    sim_result = validate_simulation()

    results["modules"] = [exp_result, rec_result, sim_result]

    all_pass = all(m["status"] == "PASS" for m in results["modules"])
    results["overall_status"] = "ALL PASS" if all_pass else "SOME FAILURES"
    results["production_ready"] = all_pass

    # Print summary
    for m in results["modules"]:
        logger.info(f"\n  {m['module']}: {m['status']}")
        for c in m["checks"]:
            icon = "✓" if c.get("pass") else "✗"
            logger.info(f"    {icon} {c['file']}")

    logger.info(f"\n  Overall: {results['overall_status']}")
    logger.info(f"  Production Ready: {results['production_ready']}")

    # Save validation report
    # Save in the project root models directory for easy access
    report_path = PROJECT_ROOT / "models" / "validation_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"\n  → Validation report: {report_path}")

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
