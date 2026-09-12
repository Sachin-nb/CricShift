"""Recommendation route — POST /api/recommend/player"""

import logging
from fastapi import APIRouter, HTTPException
from backend.dependencies import model_store
from backend.schemas import RecommendationRequest, RecommendationResponse

logger = logging.getLogger("backend")
router = APIRouter(tags=["Recommendation"])


@router.post("/api/recommend/player", response_model=RecommendationResponse,
             summary="Get player recommendations",
             description="Uses the Phase 3C recommendation engine to suggest the best next batter.")
async def recommend_player(req: RecommendationRequest):
    if not model_store.recommendation_loaded:
        raise HTTPException(503, detail="Recommendation engine not loaded")

    try:
        situation = {
            "batting_team": req.batting_team,
            "bowling_team": req.bowling_team,
            "venue": req.venue,
            "current_score": req.current_score,
            "current_wickets": req.current_wickets,
            "current_over": req.current_over,
            "required_run_rate": req.required_run_rate,
            "pressure_index": req.pressure_index,
            "momentum_score": req.momentum_score,
            "current_batter": req.current_batter,
            "current_bowler": req.current_bowler,
            "dismissed_batters": req.dismissed_batters,
        }
        recs = model_store.recommendation_engine.recommend(situation, top_n=req.top_n)
        return RecommendationResponse(
            batting_team=req.batting_team,
            scenario=f"{req.batting_team} at over {req.current_over}, "
                     f"score {req.current_score}/{req.current_wickets}",
            recommendations=recs,
        )
    except Exception as e:
        logger.exception("Recommendation failed")
        raise HTTPException(500, detail=f"Recommendation error: {str(e)}")
