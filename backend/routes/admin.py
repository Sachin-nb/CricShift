"""
Admin routes — /api/admin/*

Read-only endpoints that expose the activity database to the Next.js admin panel.
All endpoints return plain JSON (no Pydantic response_model needed since the
schemas are dynamic).  Auth is provided by the existing API-key middleware in
main.py, so these endpoints are already protected in production.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.live.activity_db import (
    get_dashboard_stats,
    get_historical_analyses,
    get_historical_analysis_by_id,
    get_live_matches,
    get_predictions,
    get_simulations,
)

logger = logging.getLogger("backend.admin")
router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard stats — single aggregated KPI object
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/stats", summary="Dashboard KPI counts")
def admin_stats() -> Dict[str, Any]:
    """
    Returns aggregate counts used by the admin dashboard KPI cards.
    Fields: total_live_matches, total_predictions, total_simulations,
            total_historical, *_today variants.
    """
    try:
        return get_dashboard_stats()
    except Exception as e:
        logger.exception("admin_stats failed")
        raise HTTPException(500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Live matches log
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/matches", summary="All observed live matches")
def admin_matches(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> List[Dict[str, Any]]:
    """
    Returns every live match that has been fetched through the system,
    ordered by last_seen_at DESC.  Includes team names, series, venue,
    fetch_count, first_seen_at, last_seen_at.
    """
    try:
        return get_live_matches(limit=limit, offset=offset)
    except Exception as e:
        logger.exception("admin_matches failed")
        raise HTTPException(500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Predictions log
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/predictions", summary="All prediction calls")
def admin_predictions(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> List[Dict[str, Any]]:
    """
    Returns every win / momentum / match prediction made via the API,
    ordered by created_at DESC.
    """
    try:
        return get_predictions(limit=limit, offset=offset)
    except Exception as e:
        logger.exception("admin_predictions failed")
        raise HTTPException(500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Simulations log
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/simulations", summary="All what-if simulation runs")
def admin_simulations(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> List[Dict[str, Any]]:
    """
    Returns every what-if simulation, including scenario name, modifications,
    original vs modified win probability and momentum class, ordered by
    created_at DESC.
    """
    try:
        return get_simulations(limit=limit, offset=offset)
    except Exception as e:
        logger.exception("admin_simulations failed")
        raise HTTPException(500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Historical analyses log
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/historical", summary="All historical CSV uploads and analyses")
def admin_historical(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> List[Dict[str, Any]]:
    """
    Returns metadata for every historical match CSV that was uploaded and
    analysed, ordered by created_at DESC.  Does NOT include the full
    timeline payload (use /api/admin/historical/{id} for that).
    """
    try:
        return get_historical_analyses(limit=limit, offset=offset)
    except Exception as e:
        logger.exception("admin_historical failed")
        raise HTTPException(500, detail=str(e))


@router.get("/historical/{analysis_id}", summary="Fetch a stored historical analysis result")
def admin_historical_detail(analysis_id: str) -> Dict[str, Any]:
    """
    Returns the full timeline + turning_points payload for a historical
    analysis by its analysis_id.  Used by the analysis result page so it
    can re-fetch data on browser refresh instead of relying on sessionStorage.
    """
    try:
        result = get_historical_analysis_by_id(analysis_id)
        if result is None:
            raise HTTPException(404, detail=f"Analysis '{analysis_id}' not found.")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("admin_historical_detail failed")
        raise HTTPException(500, detail=str(e))
