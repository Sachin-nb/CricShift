"""
Explainability Engine — Phase 3C
=================================
Generates SHAP, LIME, or tree-based explanations for the
Momentum Shift and Win Prediction models.

Auto-detects the best available explanation method:
  Priority: 1) SHAP  2) LIME  3) Tree feature importance

Produces:
  - Global feature importance (per model)
  - Local explanations (per prediction)
  - Prediction confidence
  - Positive / negative contributors
  - Top-10 feature rankings
"""

import pickle
import json
import logging
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
MOMENTUM_CLASSES = {0: "Negative", 1: "Neutral", 2: "Positive"}
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ── Helper: load model assets ─────────────────────────────────────────────────
def _load_model_assets(model_dir: Path):
    """Load model, feature columns, and label encoders from a model directory."""
    with open(model_dir / "best_model.pkl", "rb") as f:
        model = pickle.load(f)
    with open(model_dir / "feature_columns.pkl", "rb") as f:
        feature_cols = pickle.load(f)
    with open(model_dir / "label_encoder.pkl", "rb") as f:
        encoders = pickle.load(f)
    return model, feature_cols, encoders


def _encode_dataframe(df: pd.DataFrame, feature_cols: list, encoders: dict) -> pd.DataFrame:
    """Apply label encoding and prepare feature matrix exactly like predict.py."""
    df = df.copy()
    str_cols = df.select_dtypes(include=["object"]).columns.tolist()
    for col in str_cols:
        if col in encoders:
            le = encoders[col]
            df[col] = df[col].fillna("Missing").astype(str)
            df[col] = df[col].map(lambda s, _le=le: s if s in _le.classes_ else _le.classes_[0])
            df[col] = le.transform(df[col])
    df = df.fillna(0)
    df = df.replace([np.inf, -np.inf], 0)
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
    return df[feature_cols]


# ── Detect best explainer ─────────────────────────────────────────────────────
def _detect_explanation_method(model) -> str:
    """Auto-detect the best available explanation method for *model*."""
    # 1. Try SHAP TreeExplainer (works for tree-based models)
    try:
        import shap  # noqa: F401
        shap.TreeExplainer(model)
        logger.info("SHAP TreeExplainer is supported — using SHAP.")
        return "shap"
    except Exception:
        pass

    # 2. Prefer tree feature_importances_ over slow KernelExplainer
    if hasattr(model, "feature_importances_"):
        logger.info("Using built-in tree feature importances (fast fallback).")
        return "tree"

    # 3. Try LIME
    try:
        import lime  # noqa: F401
        logger.info("LIME available — using LIME.")
        return "lime"
    except ImportError:
        pass

    # 4. SHAP KernelExplainer (generic, slow — last resort)
    try:
        import shap  # noqa: F401
        logger.info("SHAP KernelExplainer (slow) — using SHAP kernel.")
        return "shap_kernel"
    except ImportError:
        pass

    logger.warning("No explainability library found; using coefficient fallback.")
    return "fallback"


# ═══════════════════════════════════════════════════════════════════════════════
class ExplainabilityEngine:
    """Unified explainability engine for both trained models."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.momentum_dir = PROJECT_ROOT / "models" / "momentum"
        self.win_dir = PROJECT_ROOT / "models" / "win_prediction"
        self.output_dir = output_dir or (PROJECT_ROOT / "models" / "explainability")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Loaded at run time
        self.momentum_model = None
        self.momentum_features: list = []
        self.momentum_encoders: dict = {}
        self.win_model = None
        self.win_features: list = []
        self.win_encoders: dict = {}

        self.method_momentum: str = ""
        self.method_win: str = ""

    # ── Load ──────────────────────────────────────────────────────────────
    def load_models(self) -> None:
        """Load both trained model assets."""
        logger.info("Loading Momentum model …")
        self.momentum_model, self.momentum_features, self.momentum_encoders = (
            _load_model_assets(self.momentum_dir)
        )
        logger.info(f"  → {len(self.momentum_features)} features")

        logger.info("Loading Win Prediction model …")
        self.win_model, self.win_features, self.win_encoders = (
            _load_model_assets(self.win_dir)
        )
        logger.info(f"  → {len(self.win_features)} features")

        # Detect methods
        self.method_momentum = _detect_explanation_method(self.momentum_model)
        self.method_win = _detect_explanation_method(self.win_model)

    # ── Global Feature Importance ─────────────────────────────────────────
    def global_feature_importance(
        self, X_momentum: pd.DataFrame, X_win: pd.DataFrame
    ) -> pd.DataFrame:
        """Compute global importance for both models and merge into one table."""
        logger.info("Computing global feature importance …")

        mom_imp = self._compute_importance(
            self.momentum_model, X_momentum, self.momentum_features, self.method_momentum, "momentum"
        )
        win_imp = self._compute_importance(
            self.win_model, X_win, self.win_features, self.method_win, "win"
        )

        # Merge
        merged = pd.merge(
            mom_imp.rename(columns={"Importance": "Momentum_Importance"}),
            win_imp.rename(columns={"Importance": "Win_Importance"}),
            on="Feature",
            how="outer",
        ).fillna(0)

        # Normalize both to [0,1] for ranking
        for col in ["Momentum_Importance", "Win_Importance"]:
            _max = merged[col].max()
            if _max > 0:
                merged[f"{col}_Norm"] = merged[col] / _max
            else:
                merged[f"{col}_Norm"] = 0

        merged["Combined_Score"] = (
            merged["Momentum_Importance_Norm"] + merged["Win_Importance_Norm"]
        ) / 2
        merged = merged.sort_values("Combined_Score", ascending=False).reset_index(drop=True)
        merged["Combined_Rank"] = merged.index + 1

        result = merged[["Feature", "Momentum_Importance", "Win_Importance", "Combined_Rank"]]

        out_path = self.output_dir / "global_feature_importance.csv"
        result.to_csv(out_path, index=False)
        logger.info(f"  → Saved {out_path}")
        return result

    def _compute_importance(
        self, model, X: pd.DataFrame, feature_cols: list, method: str, label: str
    ) -> pd.DataFrame:
        """Return a DataFrame(Feature, Importance) using the best method."""
        if method == "shap":
            return self._shap_importance(model, X, feature_cols, label)
        elif method == "shap_kernel":
            return self._shap_kernel_importance(model, X, feature_cols, label)
        elif method == "lime":
            return self._lime_global_importance(model, X, feature_cols, label)
        elif method == "tree":
            return self._tree_importance(model, feature_cols)
        else:
            return self._tree_importance(model, feature_cols)

    def _shap_importance(
        self, model, X: pd.DataFrame, feature_cols: list, label: str
    ) -> pd.DataFrame:
        """SHAP TreeExplainer-based global importance."""
        import shap

        explainer = shap.TreeExplainer(model)
        # Use a subsample to keep it fast
        sample = X.sample(n=min(500, len(X)), random_state=42)
        shap_values = explainer.shap_values(sample)

        # For multi-class, shap_values is a list; average across classes
        if isinstance(shap_values, list):
            mean_abs = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
        else:
            mean_abs = np.abs(shap_values).mean(axis=0)

        # Generate SHAP summary plot
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 8))
            if isinstance(shap_values, list):
                shap.summary_plot(shap_values, sample, feature_names=feature_cols,
                                  show=False, max_display=20)
            else:
                shap.summary_plot(shap_values, sample, feature_names=feature_cols,
                                  show=False, max_display=20)
            plot_path = self.output_dir / f"shap_summary_{label}.png"
            plt.tight_layout()
            plt.savefig(plot_path, dpi=150, bbox_inches="tight")
            plt.close("all")
            logger.info(f"  → SHAP summary plot saved: {plot_path}")
        except Exception as e:
            logger.warning(f"  Could not save SHAP plot: {e}")

        df = pd.DataFrame({"Feature": feature_cols, "Importance": mean_abs})
        return df.sort_values("Importance", ascending=False).reset_index(drop=True)

    def _shap_kernel_importance(
        self, model, X: pd.DataFrame, feature_cols: list, label: str
    ) -> pd.DataFrame:
        """SHAP KernelExplainer fallback."""
        import shap

        background = X.sample(n=min(50, len(X)), random_state=42)
        explainer = shap.KernelExplainer(model.predict_proba, background)
        sample = X.sample(n=min(100, len(X)), random_state=42)
        shap_values = explainer.shap_values(sample, nsamples=100)

        # shap_values can be: list of 2D arrays (multi-class), or a single 2D/3D array
        if isinstance(shap_values, list):
            # Multi-class: each element is (n_samples, n_features)
            mean_abs = np.mean(
                [np.abs(np.array(sv)).mean(axis=0) for sv in shap_values], axis=0
            )
        elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
            # (n_samples, n_features, n_classes)
            mean_abs = np.abs(shap_values).mean(axis=(0, 2))
        else:
            mean_abs = np.abs(np.array(shap_values)).mean(axis=0)

        # Ensure 1D
        mean_abs = np.array(mean_abs).flatten()
        if len(mean_abs) != len(feature_cols):
            logger.warning(f"SHAP kernel shape mismatch: {len(mean_abs)} vs {len(feature_cols)} features")
            mean_abs = mean_abs[:len(feature_cols)] if len(mean_abs) > len(feature_cols) else \
                np.pad(mean_abs, (0, len(feature_cols) - len(mean_abs)))

        df = pd.DataFrame({"Feature": feature_cols, "Importance": mean_abs})
        return df.sort_values("Importance", ascending=False).reset_index(drop=True)

    def _lime_global_importance(
        self, model, X: pd.DataFrame, feature_cols: list, label: str
    ) -> pd.DataFrame:
        """Approximate global importance by averaging LIME local importances."""
        from lime.lime_tabular import LimeTabularExplainer

        explainer = LimeTabularExplainer(
            X.values,
            feature_names=feature_cols,
            mode="classification",
            random_state=42,
        )
        sample = X.sample(n=min(100, len(X)), random_state=42)
        importance_acc = np.zeros(len(feature_cols))

        for _, row in sample.iterrows():
            try:
                exp = explainer.explain_instance(
                    row.values, model.predict_proba, num_features=len(feature_cols)
                )
                for feat_idx, weight in exp.as_map().get(1, exp.as_map().get(0, [])):
                    importance_acc[feat_idx] += abs(weight)
            except Exception:
                continue

        importance_acc /= max(len(sample), 1)
        df = pd.DataFrame({"Feature": feature_cols, "Importance": importance_acc})
        return df.sort_values("Importance", ascending=False).reset_index(drop=True)

    def _tree_importance(self, model, feature_cols: list) -> pd.DataFrame:
        """Built-in tree feature importances."""
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        else:
            importances = np.ones(len(feature_cols)) / len(feature_cols)
        df = pd.DataFrame({"Feature": feature_cols, "Importance": importances})
        return df.sort_values("Importance", ascending=False).reset_index(drop=True)

    # ── Local Explanations ────────────────────────────────────────────────
    def local_explanations(
        self, X_momentum: pd.DataFrame, X_win: pd.DataFrame,
        raw_df: pd.DataFrame, n_samples: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate local explanations for *n_samples* randomly chosen rows."""
        logger.info(f"Generating local explanations for {n_samples} samples …")
        indices = np.random.RandomState(42).choice(
            min(len(X_momentum), len(X_win)), size=n_samples, replace=False
        )
        explanations: List[Dict[str, Any]] = []

        for idx in indices:
            row_mom = X_momentum.iloc[[idx]]
            row_win = X_win.iloc[[idx]]
            raw_row = raw_df.iloc[idx] if idx < len(raw_df) else {}

            # Momentum prediction
            mom_pred = int(self.momentum_model.predict(row_mom)[0])
            mom_proba = self.momentum_model.predict_proba(row_mom)[0]
            mom_confidence = float(np.max(mom_proba))

            # Win prediction
            win_proba = self.win_model.predict_proba(row_win)[0]
            win_pred = int(np.argmax(win_proba))
            win_confidence = float(np.max(win_proba))
            win_prob_pct = float(win_proba[1] * 100)

            # Feature contributions
            mom_contribs = self._local_contributions(
                self.momentum_model, row_mom, self.momentum_features, self.method_momentum
            )
            win_contribs = self._local_contributions(
                self.win_model, row_win, self.win_features, self.method_win
            )

            positive_mom = [c for c in mom_contribs if c["contribution"] > 0][:5]
            negative_mom = [c for c in mom_contribs if c["contribution"] < 0][:5]
            positive_win = [c for c in win_contribs if c["contribution"] > 0][:5]
            negative_win = [c for c in win_contribs if c["contribution"] < 0][:5]

            entry = {
                "sample_index": int(idx),
                "match_context": {
                    "batting_team": str(raw_row.get("Batting_Team", "N/A")),
                    "bowling_team": str(raw_row.get("Bowling_Team", "N/A")),
                    "venue": str(raw_row.get("Venue", "N/A")),
                    "over": float(raw_row.get("Current_Over", 0)),
                    "score": float(raw_row.get("Current_Score", 0)),
                    "wickets": float(raw_row.get("Current_Wickets", 0)),
                },
                "momentum_prediction": {
                    "class": mom_pred,
                    "label": MOMENTUM_CLASSES.get(mom_pred, "Unknown"),
                    "confidence": round(mom_confidence, 4),
                    "class_probabilities": {
                        MOMENTUM_CLASSES[i]: round(float(p), 4)
                        for i, p in enumerate(mom_proba)
                    },
                    "top_10_features": mom_contribs[:10],
                    "positive_contributors": positive_mom,
                    "negative_contributors": negative_mom,
                },
                "win_prediction": {
                    "win_probability_pct": round(win_prob_pct, 2),
                    "predicted_class": win_pred,
                    "confidence": round(win_confidence, 4),
                    "class_probabilities": {
                        "Loss": round(float(win_proba[0]), 4),
                        "Win": round(float(win_proba[1]), 4),
                    },
                    "top_10_features": win_contribs[:10],
                    "positive_contributors": positive_win,
                    "negative_contributors": negative_win,
                },
            }
            explanations.append(entry)

        out_path = self.output_dir / "sample_local_explanations.json"
        with open(out_path, "w") as f:
            json.dump(explanations, f, indent=2, default=str)
        logger.info(f"  → Saved {out_path}")
        return explanations

    def _local_contributions(
        self, model, row: pd.DataFrame, feature_cols: list, method: str
    ) -> List[Dict[str, Any]]:
        """Return per-feature contributions sorted by absolute value."""
        contributions = []
        if method == "shap":
            try:
                import shap
                explainer = shap.TreeExplainer(model)
                sv = explainer.shap_values(row)
                if isinstance(sv, list):
                    # Average across classes
                    vals = np.mean([s[0] for s in sv], axis=0)
                else:
                    vals = sv[0]
                for feat, val in zip(feature_cols, vals):
                    contributions.append({
                        "feature": feat,
                        "value": round(float(row[feat].iloc[0]), 4),
                        "contribution": round(float(val), 6),
                    })
            except Exception as e:
                logger.debug(f"SHAP local failed: {e}")
                return self._tree_local_contributions(model, row, feature_cols)
        elif method == "tree":
            return self._tree_local_contributions(model, row, feature_cols)
        else:
            return self._tree_local_contributions(model, row, feature_cols)

        contributions.sort(key=lambda c: abs(c["contribution"]), reverse=True)
        return contributions

    def _tree_local_contributions(
        self, model, row: pd.DataFrame, feature_cols: list
    ) -> List[Dict[str, Any]]:
        """Approximate local contributions using global importance × feature value."""
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        else:
            importances = np.ones(len(feature_cols)) / len(feature_cols)

        contributions = []
        for feat, imp in zip(feature_cols, importances):
            val = float(row[feat].iloc[0])
            contributions.append({
                "feature": feat,
                "value": round(val, 4),
                "contribution": round(float(imp * val), 6),
            })
        contributions.sort(key=lambda c: abs(c["contribution"]), reverse=True)
        return contributions

    # ── Generate SHAP summary plot ────────────────────────────────────────
    def generate_shap_summary(self, X_win: pd.DataFrame) -> Optional[Path]:
        """Generate the canonical SHAP summary plot for the win prediction model."""
        if self.method_win not in ("shap", "shap_kernel"):
            # Generate a bar chart of tree importance instead
            return self._generate_importance_bar_chart(X_win)

        try:
            import shap
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            explainer = shap.TreeExplainer(self.win_model)
            sample = X_win.sample(n=min(500, len(X_win)), random_state=42)
            shap_values = explainer.shap_values(sample)

            plt.figure(figsize=(12, 8))
            if isinstance(shap_values, list):
                shap.summary_plot(shap_values[1], sample,
                                  feature_names=self.win_features,
                                  show=False, max_display=20)
            else:
                shap.summary_plot(shap_values, sample,
                                  feature_names=self.win_features,
                                  show=False, max_display=20)

            plot_path = self.output_dir / "shap_summary.png"
            plt.tight_layout()
            plt.savefig(plot_path, dpi=150, bbox_inches="tight")
            plt.close("all")
            logger.info(f"  → SHAP summary plot: {plot_path}")
            return plot_path
        except Exception as e:
            logger.warning(f"SHAP summary plot failed ({e}); generating bar chart instead.")
            return self._generate_importance_bar_chart(X_win)

    def _generate_importance_bar_chart(self, X_win: pd.DataFrame) -> Optional[Path]:
        """Fallback: bar chart of tree feature importances."""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            imp_df = self._tree_importance(self.win_model, self.win_features).head(20)

            fig, ax = plt.subplots(figsize=(10, 8))
            ax.barh(
                imp_df["Feature"].values[::-1],
                imp_df["Importance"].values[::-1],
                color="#2196F3",
            )
            ax.set_xlabel("Feature Importance")
            ax.set_title("Win Prediction Model — Top 20 Feature Importances")
            plt.tight_layout()

            plot_path = self.output_dir / "shap_summary.png"
            plt.savefig(plot_path, dpi=150, bbox_inches="tight")
            plt.close("all")
            logger.info(f"  → Importance bar chart saved as {plot_path}")
            return plot_path
        except Exception as e:
            logger.error(f"Could not generate importance chart: {e}")
            return None

    # ── Full report ───────────────────────────────────────────────────────
    def generate_report(
        self,
        global_imp: pd.DataFrame,
        local_explanations: List[Dict],
    ) -> Dict[str, Any]:
        """Assemble the final explainability_report.json."""
        # Load existing model metrics
        mom_metrics = {}
        win_metrics = {}
        try:
            with open(self.momentum_dir / "model_metrics.json") as f:
                mom_metrics = json.load(f)
        except Exception:
            pass
        try:
            with open(self.win_dir / "model_metrics.json") as f:
                win_metrics = json.load(f)
        except Exception:
            pass

        top10 = global_imp.head(10)["Feature"].tolist()

        report = {
            "phase": "3C",
            "module": "Explainability",
            "explanation_method": {
                "momentum_model": self.method_momentum,
                "win_prediction_model": self.method_win,
            },
            "model_performance": {
                "momentum": mom_metrics,
                "win_prediction": win_metrics,
            },
            "top_10_features_combined": top10,
            "global_feature_count": {
                "momentum": len(self.momentum_features),
                "win_prediction": len(self.win_features),
            },
            "sample_explanations_count": len(local_explanations),
            "outputs_generated": [
                "global_feature_importance.csv",
                "shap_summary.png",
                "sample_local_explanations.json",
                "explainability_report.json",
            ],
            "status": "SUCCESS",
        }

        out_path = self.output_dir / "explainability_report.json"
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"  → Report saved: {out_path}")
        return report
