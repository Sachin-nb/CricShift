import asyncio
import json
import logging
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any

from ..live.api_client import LiveAPIClient, APIClientError
from ..live.match_service import LiveMatchService
from ..live.intelligence import LiveIntelligenceService
from ..live.activity_db import log_live_match
from ..live.ws_manager import ws_manager

logger = logging.getLogger("backend.live_routes")

router = APIRouter(prefix="/api/live", tags=["live"])

def get_api_client():
    return LiveAPIClient()

def get_match_service(client: LiveAPIClient = Depends(get_api_client)):
    return LiveMatchService(client)
    
def get_intelligence_service(client: LiveAPIClient = Depends(get_api_client)):
    return LiveIntelligenceService(client)


@router.get("/matches", response_model=List[Dict[str, Any]])
def get_live_matches(match_service: LiveMatchService = Depends(get_match_service)):
    """Returns currently live matches."""
    matches = match_service.get_live_matches()
    # Log every seen match into the activity DB (upsert by match_id)
    for m in matches:
        try:
            log_live_match(m)
        except Exception:
            pass
    return matches

@router.get("/match/{match_id}")
def get_live_match_state(
    match_id: str,
    client: LiveAPIClient = Depends(get_api_client)
):
    """
    Returns detailed normalized live match information.
    Enriches the raw normalizer state with convenience fields consumed by the
    frontend live/[matchId]/page.tsx:
      - team_a / team_b          (same as batting_team / bowling_team)
      - batting_team / bowling_team
      - target
      - match_format
      - team_a_score / team_b_score  (formatted score strings for MatchCard)
    """
    try:
        scorecard    = client.get_scorecard(match_id)
        over_history = client.get_over_history(match_id)
        commentary   = client.get_commentary(match_id)

        from ..live.normalizer import normalize_live_data
        from ..live.match_service import _extract_innings_scores
        state = normalize_live_data(scorecard, over_history, commentary)
        state["match_id"] = match_id

        # Convenience aliases the frontend page reads via `match.team_a` / `match.team_b`
        batting_team = state.get("batting_team") or "Team A"
        bowling_team = state.get("bowling_team") or "Team B"
        state["team_a"] = batting_team
        state["team_b"] = bowling_team

        # Formatted score strings for the MatchCard component
        score    = state.get("current_score", 0)
        wickets  = state.get("current_wickets", 0)
        overs    = state.get("overs", 0)
        target   = state.get("target", 0)

        state["team_a_score"] = f"{score}/{wickets}"
        state["team_a_overs"] = str(overs)

        # team_b (bowling side) — prefer its ACTUAL completed-innings score from
        # the scorecard rather than only showing "Target: N". Fall back to the
        # target line, then to a friendly placeholder — never a bare "-".
        bowling_innings = None
        try:
            all_innings = _extract_innings_scores(scorecard)
            # the bowling team's innings, matched by name (case-insensitive/substring)
            low = bowling_team.lower()
            for name, data in all_innings.items():
                if name.lower() == low or low in name.lower() or name.lower() in low:
                    bowling_innings = data
                    break
        except Exception:
            bowling_innings = None

        if bowling_innings:
            b_over = bowling_innings.get("overs", "")
            over_suffix = f" ({b_over})" if b_over not in ("", "0", "0.0", 0, None) else ""
            state["team_b_score"] = f"{bowling_innings['score']}/{bowling_innings['wickets']}{over_suffix}"
            state["team_b_overs"] = ""
        elif target > 0:
            state["team_b_score"] = f"Target: {target}"
            state["team_b_overs"] = ""
        else:
            state["team_b_score"] = "Yet to bat"
            state["team_b_overs"] = ""

        # Real innings length derived from the live feed (falls back to T20).
        mo = int(state.get("max_overs", 0) or 0)
        state["max_overs"] = mo
        state["match_format"] = "ODI" if mo >= 40 else "T20"

        return state
    except APIClientError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error normalizing match state: {e}")

@router.get("/match/{match_id}/intelligence")
def get_match_intelligence(
    match_id: str,
    intel_service: LiveIntelligenceService = Depends(get_intelligence_service)
):
    """
    Returns live state + momentum prediction + win prediction.
    """
    result = intel_service.get_live_intelligence(match_id)
    if "error" in result:
        status = 502 if result["error"] == "API Error" else 500
        raise HTTPException(status_code=status, detail=result.get("details", result["error"]))
    return result


@router.websocket("/ws/{match_id}")
async def live_websocket_endpoint(
    websocket: WebSocket,
    match_id: str,
):
    """
    WebSocket endpoint for real-time live match intelligence streaming.
    Clients receive an immediate initial payload and live updates/heartbeats.
    """
    await ws_manager.connect(match_id, websocket)
    intel_service = LiveIntelligenceService()
    try:
        # Send initial match intelligence payload immediately
        try:
            intel = intel_service.get_live_intelligence(match_id)
            await websocket.send_json({
                "type": "initial_state",
                "match_id": match_id,
                "data": intel,
            })
        except Exception as e:
            logger.warning(f"Failed to send initial intelligence over WebSocket for {match_id}: {e}")
            await websocket.send_json({
                "type": "error",
                "match_id": match_id,
                "detail": str(e),
            })

        # Keep connection open, handle client requests and push periodic updates
        while True:
            try:
                # Wait for client messages with 10s timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
                try:
                    payload = json.loads(data)
                    action = payload.get("action")
                    if action == "refresh":
                        intel = intel_service.get_live_intelligence(match_id)
                        await websocket.send_json({
                            "type": "refresh",
                            "match_id": match_id,
                            "data": intel,
                        })
                    elif action == "ping":
                        await websocket.send_json({"type": "pong"})
                except Exception as parse_err:
                    logger.debug(f"Non-JSON or invalid client message: {parse_err}")
            except asyncio.TimeoutError:
                # Heartbeat / live poll push
                try:
                    intel = intel_service.get_live_intelligence(match_id)
                    await websocket.send_json({
                        "type": "update",
                        "match_id": match_id,
                        "data": intel,
                    })
                except Exception:
                    await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        await ws_manager.disconnect(match_id, websocket)
    except Exception as e:
        logger.info(f"WebSocket closed for {match_id}: {e}")
        await ws_manager.disconnect(match_id, websocket)

