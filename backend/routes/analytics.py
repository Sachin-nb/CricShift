"""Analytics routes — read-only data endpoints."""

import logging
import math
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.dependencies import model_store

logger = logging.getLogger("backend")
router = APIRouter(tags=["Analytics"])


def _clean(val):
    """Replace NaN/Inf with None for JSON serialisation."""
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val


def _clean_records(records: list) -> list:
    """Clean all values in a list of dicts returned by DataFrame.to_dict('records')."""
    return [{k: _clean(v) for k, v in row.items()} for row in records]


@router.get(
    "/api/analytics/players",
    summary="List player statistics",
    description="Returns player stats from Phase 2B. Supports search and pagination.",
)
async def get_players(
    search: Optional[str] = Query(None, description="Search by player name"),
    min_matches: int = Query(0, ge=0, description="Minimum matches played"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    if not model_store.data_loaded:
        raise HTTPException(503, detail="Reference data not loaded")

    df = model_store.player_stats.copy()
    if search:
        df = df[df["Player_Name"].str.contains(search, case=False, na=False)]
    if min_matches > 0:
        df = df[df["Matches_Played"] >= min_matches]

    total = len(df)
    # Validate that offset does not exceed total rows
    effective_offset = min(offset, total)
    df = df.iloc[effective_offset: effective_offset + limit]

    return {
        "total": total,
        "players": _clean_records(df.to_dict("records")),
    }


@router.get(
    "/api/analytics/teams",
    summary="List team statistics",
    description="Returns team stats from Phase 2B.",
)
async def get_teams(
    search: Optional[str] = Query(None, description="Search by team name"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    if not model_store.data_loaded:
        raise HTTPException(503, detail="Reference data not loaded")

    df = model_store.team_stats.copy()
    if search:
        df = df[df["Team"].str.contains(search, case=False, na=False)]

    total = len(df)
    effective_offset = min(offset, total)
    df = df.iloc[effective_offset: effective_offset + limit]

    return {
        "total": total,
        "teams": _clean_records(df.to_dict("records")),
    }


@router.get(
    "/api/analytics/venues",
    summary="List venue statistics",
    description="Returns venue stats from Phase 2B.",
)
async def get_venues(
    search: Optional[str] = Query(None, description="Search by venue name"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    if not model_store.data_loaded:
        raise HTTPException(503, detail="Reference data not loaded")

    df = model_store.venue_stats.copy()
    if search:
        df = df[df["Venue"].str.contains(search, case=False, na=False)]

    total = len(df)
    effective_offset = min(offset, total)
    df = df.iloc[effective_offset: effective_offset + limit]

    return {
        "total": total,
        "venues": _clean_records(df.to_dict("records")),
    }


@router.get(
    "/api/analytics/matchup",
    summary="Get head-to-head batter vs bowler matchup",
    description="Returns detailed historical head-to-head statistics between a batter and bowler.",
)
async def get_matchup_endpoint(
    batter: str = Query(..., description="Batter name"),
    bowler: str = Query(..., description="Bowler name"),
):
    from backend.live.db import get_matchup
    matchup = get_matchup(batter, bowler)
    if not matchup:
        return {
            "found": False,
            "batter": batter,
            "bowler": bowler,
            "message": f"No historical head-to-head records found between {batter} and {bowler}.",
        }
    return {
        "found": True,
        "matchup": _clean_records([matchup])[0],
    }


@router.get(
    "/api/analytics/matchups",
    summary="List player matchups",
    description="Returns head-to-head matchups for a given batter or bowler.",
)
async def get_player_matchups_endpoint(
    batter: Optional[str] = Query(None, description="Batter name"),
    bowler: Optional[str] = Query(None, description="Bowler name"),
    min_balls: int = Query(1, ge=0, description="Minimum balls faced"),
    limit: int = Query(25, ge=1, le=100),
):
    from backend.live.db import get_batter_matchups, get_bowler_matchups
    if batter:
        records = get_batter_matchups(batter, min_balls=min_balls, limit=limit)
        return {
            "player_type": "batter",
            "player_name": batter,
            "count": len(records),
            "matchups": _clean_records(records),
        }
    elif bowler:
        records = get_bowler_matchups(bowler, min_balls=min_balls, limit=limit)
        return {
            "player_type": "bowler",
            "player_name": bowler,
            "count": len(records),
            "matchups": _clean_records(records),
        }
    else:
        raise HTTPException(400, detail="Must provide either 'batter' or 'bowler' query parameter.")


@router.get(
    "/api/analytics/matchups/matrix",
    summary="Get 2D matchup matrix for team line-ups",
    description="Accepts comma-separated list of batters and bowlers and returns pairwise matchup records.",
)
async def get_matchup_matrix_endpoint(
    batters: str = Query(..., description="Comma-separated batter names"),
    bowlers: str = Query(..., description="Comma-separated bowler names"),
):
    from backend.live.db import get_matchup_matrix
    bat_list = [b.strip() for b in batters.split(",") if b.strip()]
    bowl_list = [b.strip() for b in bowlers.split(",") if b.strip()]
    if not bat_list or not bowl_list:
        raise HTTPException(400, detail="Both batters and bowlers lists must be non-empty.")

    records = get_matchup_matrix(bat_list, bowl_list)
    return {
        "batters": bat_list,
        "bowlers": bowl_list,
        "total_records": len(records),
        "matrix": _clean_records(records),
    }

