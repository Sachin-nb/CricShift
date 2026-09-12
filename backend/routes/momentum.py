"""Momentum route — POST /api/predict/momentum"""

import logging
from fastapi import APIRouter, HTTPException
from backend.dependencies import model_store
from backend.schemas import MatchStateRequest, MomentumResponse
from backend.live.activity_db import log_prediction

logger = logging.getLogger("backend")
router = APIRouter(tags=["Prediction"])


@router.post(
    "/api/predict/momentum",
    response_model=MomentumResponse,
    summary="Predict momentum state",
    description="Uses the Phase 3A momentum-shift model to classify the current match momentum.",
)
async def predict_momentum(req: MatchStateRequest):
    if not model_store.momentum_loaded:
        raise HTTPException(503, detail="Momentum model not loaded")

    try:
        feature_row = model_store.build_feature_row(req.model_dump())
        result = model_store.predict_momentum(feature_row)

        try:
            log_prediction("momentum", req.model_dump(), result)
        except Exception:
            pass

        return MomentumResponse(**result)
    except Exception as e:
        logger.exception("Momentum prediction failed")
        raise HTTPException(500, detail=f"Prediction error: {str(e)}")


@router.post(
    "/api/predict/match",
    summary="Combined match intelligence",
    description="Returns win probability, momentum, and key indicators in a single call.",
)
async def predict_match(req: MatchStateRequest):
    if not (model_store.momentum_loaded and model_store.win_loaded):
        raise HTTPException(503, detail="One or more models not loaded")

    try:
        feature_row = model_store.build_feature_row(req.model_dump())
        win_result = model_store.predict_win(feature_row, req.batting_team, req.bowling_team)
        mom_result = model_store.predict_momentum(feature_row)

        balls_bowled = req.current_over * 6 + req.current_ball
        crr = (req.current_score / balls_bowled * 6) if balls_bowled > 0 else 0
        rrr = 0.0
        if req.target > 0 and (120 - balls_bowled) > 0:
            rrr = max(0, req.target - req.current_score) / (120 - balls_bowled) * 6

        combined = {
            "match_state": {
                "batting_team": req.batting_team,
                "bowling_team": req.bowling_team,
                "venue": req.venue,
                "innings": req.innings,
                "score": f"{req.current_score}/{req.current_wickets}",
                "over": f"{req.current_over}.{req.current_ball}",
                "current_run_rate": round(crr, 2),
                "required_run_rate": round(rrr, 2),
            },
            "win_probability": win_result["win_probability"],
            "predicted_winner": win_result["predicted_winner"],
            "momentum": {
                "class": mom_result["momentum_class"],
                "probabilities": mom_result["probabilities"],
            },
            "confidence": {
                "win_model": win_result["confidence"],
                "momentum_model": mom_result["confidence"],
            },
            "key_indicators": {
                "current_run_rate": round(crr, 2),
                "required_run_rate": round(rrr, 2),
                "wickets_remaining": 10 - req.current_wickets,
                "balls_remaining": max(0, 120 - balls_bowled),
                "momentum_class": mom_result["momentum_class"],
            },
        }

        # Log as a combined prediction
        try:
            merged = {**win_result, "momentum_class": mom_result["momentum_class"]}
            log_prediction("match", req.model_dump(), merged)
        except Exception:
            pass

        return combined

    except Exception as e:
        logger.exception("Combined prediction failed")
        raise HTTPException(500, detail=f"Prediction error: {str(e)}")
