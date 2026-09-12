"""
Phase 4 — Backend Test Suite
Uses pytest + FastAPI TestClient for compact endpoint tests.

Run:  pytest tests/test_backend.py -v
"""

import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import BACKEND_API_KEY


@pytest.fixture(scope="session")
def client():
    """Create a TestClient that triggers the lifespan (model loading)."""
    headers = {"X-API-Key": BACKEND_API_KEY} if BACKEND_API_KEY else {}
    with TestClient(app, headers=headers) as c:
        yield c


# ═════════════════════════════════════════════════════════════════════
# SHARED PAYLOADS
# ═════════════════════════════════════════════════════════════════════

VALID_MATCH_STATE = {
    "batting_team": "Mumbai Indians",
    "bowling_team": "Chennai Super Kings",
    "venue": "Wankhede Stadium",
    "innings": 2,
    "current_over": 12,
    "current_ball": 3,
    "current_score": 95,
    "current_wickets": 3,
    "target": 180,
    "batter_name": "Rohit Sharma",
    "bowler_name": "DJ Bravo",
    "season": "2023",
    "runs_last_6_balls": 8,
    "runs_last_12_balls": 14,
    "runs_last_30_balls": 35,
}

VALID_REC_REQUEST = {
    "batting_team": "Mumbai Indians",
    "bowling_team": "Chennai Super Kings",
    "venue": "Wankhede Stadium",
    "current_score": 140,
    "current_wickets": 5,
    "current_over": 16,
    "required_run_rate": 12.5,
    "pressure_index": 72.0,
    "momentum_score": -15.0,
    "current_batter": "Rohit Sharma",
    "current_bowler": "DJ Bravo",
    "dismissed_batters": ["SA Yadav", "Ishan Kishan"],
    "top_n": 5,
}

VALID_EXPLAIN_REQUEST = {
    "batting_team": "Mumbai Indians",
    "bowling_team": "Chennai Super Kings",
    "venue": "Wankhede Stadium",
    "innings": 2,
    "current_over": 12,
    "current_ball": 3,
    "current_score": 95,
    "current_wickets": 3,
    "target": 180,
    "model": "both",
}

VALID_SIM_REQUEST = {
    "batting_team": "Mumbai Indians",
    "bowling_team": "Chennai Super Kings",
    "venue": "Wankhede Stadium",
    "innings": 2,
    "current_over": 12,
    "current_ball": 3,
    "current_score": 95,
    "current_wickets": 3,
    "target": 180,
    "batter_name": "Rohit Sharma",
    "bowler_name": "DJ Bravo",
    "modifications": {"replace_batter": "AB de Villiers"},
    "scenario_name": "Replace batter with power-hitter",
}


# ═════════════════════════════════════════════════════════════════════
# 1. HEALTH
# ═════════════════════════════════════════════════════════════════════

def test_health_returns_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "cricket-analytics-api"
    assert isinstance(body["models_loaded"], bool)
    assert "model_status" in body


def test_root_returns_info(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "docs" in r.json()


def test_auth_unauthorized():
    if BACKEND_API_KEY:
        with TestClient(app) as unauth_client:
            r = unauth_client.post("/api/predict/win", json=VALID_MATCH_STATE)
            assert r.status_code == 401


# ═════════════════════════════════════════════════════════════════════
# 2. WIN PREDICTION
# ═════════════════════════════════════════════════════════════════════

def test_win_prediction_valid(client):
    r = client.post("/api/predict/win", json=VALID_MATCH_STATE)
    assert r.status_code == 200
    body = r.json()
    assert "win_probability" in body
    assert "predicted_winner" in body
    assert "confidence" in body
    probs = body["win_probability"]
    total = sum(probs.values())
    assert 99 < total < 101


def test_win_prediction_missing_field(client):
    bad = {"bowling_team": "CSK", "current_over": 5, "current_score": 40, "current_wickets": 2}
    r = client.post("/api/predict/win", json=bad)
    assert r.status_code == 422


def test_win_prediction_negative_runs(client):
    bad = {**VALID_MATCH_STATE, "current_score": -10}
    r = client.post("/api/predict/win", json=bad)
    assert r.status_code == 422


def test_win_prediction_invalid_wickets(client):
    bad = {**VALID_MATCH_STATE, "current_wickets": 11}
    r = client.post("/api/predict/win", json=bad)
    assert r.status_code == 422


def test_win_prediction_invalid_over(client):
    bad = {**VALID_MATCH_STATE, "current_over": 25}
    r = client.post("/api/predict/win", json=bad)
    assert r.status_code == 422


def test_win_prediction_innings2_no_target(client):
    bad = {**VALID_MATCH_STATE, "innings": 2, "target": 0}
    r = client.post("/api/predict/win", json=bad)
    assert r.status_code == 422


# ═════════════════════════════════════════════════════════════════════
# 3. MOMENTUM
# ═════════════════════════════════════════════════════════════════════

def test_momentum_valid(client):
    r = client.post("/api/predict/momentum", json=VALID_MATCH_STATE)
    assert r.status_code == 200
    body = r.json()
    assert body["momentum_class"] in ("Positive", "Neutral", "Negative")
    assert "probabilities" in body
    assert body["confidence"] > 0


def test_momentum_invalid_input(client):
    r = client.post("/api/predict/momentum", json={})
    assert r.status_code == 422


# ═════════════════════════════════════════════════════════════════════
# 4. COMBINED PREDICTION
# ═════════════════════════════════════════════════════════════════════

def test_match_intelligence(client):
    r = client.post("/api/predict/match", json=VALID_MATCH_STATE)
    assert r.status_code == 200
    body = r.json()
    assert "win_probability" in body
    assert "momentum" in body
    assert "confidence" in body
    assert "key_indicators" in body
    assert "match_state" in body


# ═════════════════════════════════════════════════════════════════════
# 5. RECOMMENDATION
# ═════════════════════════════════════════════════════════════════════

def test_recommendation_valid(client):
    r = client.post("/api/recommend/player", json=VALID_REC_REQUEST)
    assert r.status_code == 200
    body = r.json()
    assert "recommendations" in body
    assert len(body["recommendations"]) <= 5
    for rec in body["recommendations"]:
        assert "Player" in rec
        assert "Recommendation_Score" in rec
        assert rec["Recommendation_Score"] >= 0
        assert "Confidence" in rec


def test_recommendation_missing_team(client):
    bad = {**VALID_REC_REQUEST}
    del bad["batting_team"]
    r = client.post("/api/recommend/player", json=bad)
    assert r.status_code == 422


# ═════════════════════════════════════════════════════════════════════
# 6. EXPLAINABILITY
# ═════════════════════════════════════════════════════════════════════

def test_explainability_valid(client):
    r = client.post("/api/explain", json=VALID_EXPLAIN_REQUEST)
    assert r.status_code == 200
    body = r.json()
    assert "predictions" in body
    assert "feature_contributions" in body
    assert "top_features" in body
    assert body["model_used"] == "both"


# ═════════════════════════════════════════════════════════════════════
# 7. SIMULATION
# ═════════════════════════════════════════════════════════════════════

def test_simulation_valid(client):
    r = client.post("/api/simulate", json=VALID_SIM_REQUEST)
    assert r.status_code == 200
    body = r.json()
    assert "original" in body
    assert "modified" in body
    assert "delta" in body
    assert "explanation" in body
    assert "win_probability_pct" in body["original"]
    assert "win_probability_pct" in body["modified"]


def test_simulation_missing_modifications(client):
    bad = {**VALID_SIM_REQUEST}
    del bad["modifications"]
    r = client.post("/api/simulate", json=bad)
    assert r.status_code == 422


# ═════════════════════════════════════════════════════════════════════
# 8. ANALYTICS
# ═════════════════════════════════════════════════════════════════════

def test_analytics_players(client):
    r = client.get("/api/analytics/players")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body
    assert "players" in body
    assert body["total"] > 0


def test_analytics_player_search(client):
    r = client.get("/api/analytics/players?search=Kohli")
    assert r.status_code == 200


def test_analytics_teams(client):
    r = client.get("/api/analytics/teams")
    assert r.status_code == 200
    assert r.json()["total"] > 0


def test_analytics_venues(client):
    r = client.get("/api/analytics/venues")
    assert r.status_code == 200
    assert r.json()["total"] > 0


# ═════════════════════════════════════════════════════════════════════
# 9. EDGE CASES & VALIDATION
# ═════════════════════════════════════════════════════════════════════

def test_malformed_json(client):
    r = client.post("/api/predict/win", content="not json",
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 422


def test_nonexistent_endpoint(client):
    r = client.get("/api/nonexistent")
    assert r.status_code in (404, 405)


def test_docs_accessible(client):
    r = client.get("/docs")
    assert r.status_code == 200


def test_redoc_accessible(client):
    r = client.get("/redoc")
    assert r.status_code == 200


# ═════════════════════════════════════════════════════════════════════
# 10. ARCHITECTURAL UPGRADES (Monte Carlo, Commentary, Matchups, WS)
# ═════════════════════════════════════════════════════════════════════

def test_monte_carlo_simulation(client):
    payload = {
        "current_score": 120,
        "current_wickets": 3,
        "current_over": 15,
        "current_ball": 0,
        "target": 170,
        "num_simulations": 200,
        "batter_name": "V Kohli",
        "bowler_name": "JJ Bumrah",
    }
    r = client.post("/api/simulate/monte-carlo", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["simulations_run"] == 200
    assert 0.0 <= data["win_probability_pct"] <= 100.0
    assert data["median_score"] >= 120
    assert "percentiles" in data
    assert "score_distribution" in data
    assert len(data["score_distribution"]) > 0


def test_ai_commentary_generation(client):
    payload = {
        "batting_team": "Royal Challengers Bangalore",
        "bowling_team": "Mumbai Indians",
        "current_over": 18,
        "current_ball": 4,
        "current_score": 165,
        "current_wickets": 5,
        "target": 185,
        "win_prob_batting": 38.5,
        "win_prob_delta": -14.2,
        "momentum_label": "Negative",
        "batter_name": "V Kohli",
        "bowler_name": "JJ Bumrah",
        "top_shap_features": ["pressure_index", "required_run_rate"],
    }
    r = client.post("/api/commentary/generate", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "headline" in data
    assert "commentary" in data
    assert "tactical_insight" in data
    assert data["tone"] in ["CRITICAL", "MOMENTUM_SHIFT", "TACTICAL_PRESSURE", "DOMINANT", "BALANCED"]
    assert 1 <= data["impact_rating"] <= 10


def test_analytics_matchup_specific(client):
    r = client.get("/api/analytics/matchup?batter=V%20Kohli&bowler=JJ%20Bumrah")
    assert r.status_code == 200
    data = r.json()
    assert data["found"] is True
    assert "matchup" in data
    assert data["matchup"]["Batter"] == "V Kohli"
    assert data["matchup"]["Bowler"] == "JJ Bumrah"
    assert data["matchup"]["Balls_Faced"] > 0


def test_analytics_matchup_not_found(client):
    r = client.get("/api/analytics/matchup?batter=NonExistentPlayer999&bowler=UnknownBowler888")
    assert r.status_code == 200
    data = r.json()
    assert data["found"] is False


def test_analytics_player_matchups(client):
    r = client.get("/api/analytics/matchups?batter=V%20Kohli&min_balls=5&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert data["player_type"] == "batter"
    assert len(data["matchups"]) > 0


def test_analytics_matchup_matrix(client):
    r = client.get("/api/analytics/matchups/matrix?batters=V%20Kohli,RG%20Sharma&bowlers=JJ%20Bumrah,SP%20Narine")
    assert r.status_code == 200
    data = r.json()
    assert "matrix" in data
    assert len(data["batters"]) == 2
    assert len(data["bowlers"]) == 2


def test_historical_analysis_not_found(client):
    r = client.get("/api/historical/analysis/nonexistent_id_999")
    assert r.status_code == 404


def test_live_websocket(client):
    with client.websocket_connect("/api/live/ws/test_match_123") as ws:
        data = ws.receive_json()
        assert "type" in data
        assert data["match_id"] == "test_match_123"


def test_historical_upload_cricsheet_csv(client):
    csv_path = "data/raw/ipl_male_csv/1082591.csv"
    with open(csv_path, "rb") as f:
        r = client.post(
            "/api/historical/upload",
            files={"file": ("1082591.csv", f, "text/csv")}
        )
    assert r.status_code == 200
    data = r.json()
    assert "match_info" in data
    assert data["match_info"]["winner"] == "Sunrisers Hyderabad"
    assert "35 runs" in data["match_info"]["result_description"]
    assert "207" in data["match_info"]["team_a_score"]
    assert "172" in data["match_info"]["team_b_score"]
    assert data["match_info"]["target"] == 208
    assert len(data["timeline"]) > 0
    assert len(data["turning_points"]) > 0


