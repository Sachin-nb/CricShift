"""
Run Explainability Pipeline — Phase 3C
========================================
Loads sample data, runs the ExplainabilityEngine on both trained models,
and generates all output artefacts.

Usage:
    python -m models.explainability.run_explainability
"""

import logging
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.explainability.explainability_engine import (
    ExplainabilityEngine,
    _encode_dataframe,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("=" * 60)
    logger.info("  Phase 3C — Explainability Pipeline")
    logger.info("=" * 60)

    # ── 1. Initialise engine & load models ────────────────────────────────
    engine = ExplainabilityEngine()
    engine.load_models()

    # ── 2. Load sample data ───────────────────────────────────────────────
    feature_path = PROJECT_ROOT / "data" / "features" / "feature_dataset.csv"
    logger.info(f"Loading sample data from {feature_path} …")
    raw_df = pd.read_csv(feature_path, nrows=5000)
    logger.info(f"  → Loaded {len(raw_df)} rows, {len(raw_df.columns)} columns")

    # ── 3. Prepare feature matrices ──────────────────────────────────────
    X_momentum = _encode_dataframe(raw_df, engine.momentum_features, engine.momentum_encoders)
    X_win = _encode_dataframe(raw_df, engine.win_features, engine.win_encoders)
    logger.info(f"  → Momentum matrix: {X_momentum.shape}")
    logger.info(f"  → Win matrix:      {X_win.shape}")

    # ── 4. Global feature importance ─────────────────────────────────────
    global_imp = engine.global_feature_importance(X_momentum, X_win)
    logger.info(f"  → Top 5 combined features: {global_imp.head(5)['Feature'].tolist()}")

    # ── 5. SHAP summary plot ─────────────────────────────────────────────
    engine.generate_shap_summary(X_win)

    # ── 6. Local explanations ────────────────────────────────────────────
    local_exps = engine.local_explanations(X_momentum, X_win, raw_df, n_samples=5)

    # ── 7. Final report ──────────────────────────────────────────────────
    report = engine.generate_report(global_imp, local_exps)

    logger.info("=" * 60)
    logger.info("  Explainability pipeline complete")
    logger.info(f"  Method (momentum): {engine.method_momentum}")
    logger.info(f"  Method (win):      {engine.method_win}")
    logger.info(f"  Outputs in:        {engine.output_dir}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
