"""Win-prediction route — POST /api/predict/win"""

import logging
from fastapi import APIRouter, HTTPException
from backend.dependencies import model_store
from backend.schemas import MatchStateRequest, WinProbabilityResponse
from backend.live.activity_db import log_prediction

logger = logging.getLogger("backend")
router = APIRouter(tags=["Prediction"])


@router.post(
    "/api/predict/win",
    response_model=WinProbabilityResponse,
    summary="Predict win probability",
    description="Uses the Phase 3B calibrated win-prediction model.",
)
async def predict_win(req: MatchStateRequest):
    if not model_store.win_loaded:
        raise HTTPException(503, detail="Win prediction model not loaded")

    try:
        feature_row = model_store.build_feature_row(req.model_dump())
        result = model_store.predict_win(feature_row, req.batting_team, req.bowling_team)

        try:
            log_prediction("win", req.model_dump(), result)
        except Exception:
            pass

        return WinProbabilityResponse(**result)
    except Exception as e:
        logger.exception("Win prediction failed")
        raise HTTPException(500, detail=f"Prediction error: {str(e)}")
