"""Explainability route — POST /api/explain"""

import logging
import numpy as np
from fastapi import APIRouter, HTTPException
from backend.dependencies import model_store
from backend.config import MOMENTUM_LABELS
from backend.schemas import (
    ExplainRequest, ExplainResponse,
    CommentaryRequest, CommentaryResponse,
)
from backend.live.commentary_engine import commentary_engine

logger = logging.getLogger("backend")
router = APIRouter(tags=["Explainability"])


@router.post(
    "/api/explain",
    response_model=ExplainResponse,
    summary="Explain model predictions",
    description=(
        "Returns feature contributions and importance for a given match state "
        "using Phase 3C explainability. The 'model' field accepts 'momentum', "
        "'win', or 'both'."
    ),
)
async def explain(req: ExplainRequest):
    if not (model_store.momentum_loaded and model_store.win_loaded):
        raise HTTPException(503, detail="Models not loaded")

    try:
        feature_row = model_store.build_feature_row(req.model_dump())
        predictions: dict = {}
        contributions: dict = {}
        top_features: list = []

        if req.model in ("momentum", "both"):
            # Use the public encode() method — not a private internal
            mom_enc = model_store.encode(
                feature_row, model_store.momentum_features, model_store.momentum_encoders
            )
            mom_pred = int(model_store.momentum_model.predict(mom_enc)[0])
            mom_proba = model_store.momentum_model.predict_proba(mom_enc)[0]
            predictions["momentum"] = {
                "class": MOMENTUM_LABELS.get(mom_pred, "Unknown"),
                "confidence": round(float(np.max(mom_proba)), 4),
                "probabilities": {
                    MOMENTUM_LABELS[i]: round(float(p), 4)
                    for i, p in enumerate(mom_proba)
                },
            }
            if hasattr(model_store.momentum_model, "feature_importances_"):
                imp = model_store.momentum_model.feature_importances_
                feat_imp = sorted(
                    zip(model_store.momentum_features, imp), key=lambda x: -x[1]
                )
                contributions["momentum"] = [
                    {
                        "feature": f,
                        "importance": round(float(v), 6),
                        "value": round(float(mom_enc[f].iloc[0]), 4),
                    }
                    for f, v in feat_imp[:10]
                ]
                top_features.extend([f for f, _ in feat_imp[:5]])

        if req.model in ("win", "both"):
            win_enc = model_store.encode(
                feature_row, model_store.win_features, model_store.win_encoders
            )
            win_proba = model_store.win_model.predict_proba(win_enc)[0]
            predictions["win"] = {
                "win_probability_pct": round(float(win_proba[1]) * 100, 2),
                "confidence": round(float(np.max(win_proba)), 4),
                "probabilities": {
                    "Loss": round(float(win_proba[0]), 4),
                    "Win": round(float(win_proba[1]), 4),
                },
            }
            # Use pre-loaded global feature importance (loaded once at startup,
            # not per-request from disk)
            imp_df = model_store.global_feature_importance
            if imp_df is not None and not imp_df.empty:
                contributions["win"] = [
                    {
                        "feature": row["Feature"],
                        "importance": round(float(row["Win_Importance"]), 6),
                    }
                    for row in imp_df.head(10).to_dict("records")
                ]
                top_features.extend(imp_df.head(5)["Feature"].tolist())
            else:
                contributions["win"] = []

        # Deduplicate top features while preserving order
        seen: set = set()
        unique_top: list = []
        for f in top_features:
            if f not in seen:
                unique_top.append(f)
                seen.add(f)

        return ExplainResponse(
            model_used=req.model,
            predictions=predictions,
            feature_contributions=contributions,
            top_features=unique_top[:10],
        )
    except Exception as e:
        logger.exception("Explainability failed")
        raise HTTPException(500, detail=f"Explainability error: {str(e)}")


@router.post(
    "/api/commentary/generate",
    response_model=CommentaryResponse,
    summary="Generate AI contextual broadcast commentary",
    description=(
        "Synthesizes match state, win probability deltas, and SHAP top feature drivers "
        "into broadcast-ready commentary and tactical insights."
    ),
)
async def generate_commentary(req: CommentaryRequest):
    try:
        res = commentary_engine.generate_commentary(
            batting_team=req.batting_team,
            bowling_team=req.bowling_team,
            current_over=req.current_over,
            current_ball=req.current_ball,
            current_score=req.current_score,
            current_wickets=req.current_wickets,
            target=req.target,
            win_prob_batting=req.win_prob_batting,
            win_prob_delta=req.win_prob_delta,
            momentum_label=req.momentum_label,
            batter_name=req.batter_name,
            bowler_name=req.bowler_name,
            top_shap_features=req.top_shap_features,
        )
        return CommentaryResponse(**res)
    except Exception as e:
        logger.exception("Commentary generation failed")
        raise HTTPException(500, detail=f"Commentary error: {str(e)}")

