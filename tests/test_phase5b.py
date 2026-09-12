import pytest
from backend.live.api_client import LiveAPIClient, APIClientError
from backend.live.match_service import LiveMatchService
from backend.live.normalizer import _parse_ball_event, normalize_live_data
from backend.live.intelligence import LiveIntelligenceService
import os

def test_ball_event_parsing():
    # Normal runs
    assert _parse_ball_event("1") == {"runs": 1, "is_wicket": 0, "is_boundary": 0, "is_dot": 0, "is_extra": 0}
    assert _parse_ball_event("4") == {"runs": 4, "is_wicket": 0, "is_boundary": 1, "is_dot": 0, "is_extra": 0}
    assert _parse_ball_event("6") == {"runs": 6, "is_wicket": 0, "is_boundary": 1, "is_dot": 0, "is_extra": 0}
    
    # Dot ball
    assert _parse_ball_event("0") == {"runs": 0, "is_wicket": 0, "is_boundary": 0, "is_dot": 1, "is_extra": 0}
    
    # Wickets
    assert _parse_ball_event("W") == {"runs": 0, "is_wicket": 1, "is_boundary": 0, "is_dot": 0, "is_extra": 0}
    assert _parse_ball_event("1W") == {"runs": 1, "is_wicket": 1, "is_boundary": 0, "is_dot": 0, "is_extra": 0}
    
    # Extras
    assert _parse_ball_event("1LB") == {"runs": 1, "is_wicket": 0, "is_boundary": 0, "is_dot": 0, "is_extra": 1}
    assert _parse_ball_event("wd") == {"runs": 0, "is_wicket": 0, "is_boundary": 0, "is_dot": 0, "is_extra": 1}
    assert _parse_ball_event("1WD") == {"runs": 1, "is_wicket": 0, "is_boundary": 0, "is_dot": 0, "is_extra": 1}

def test_live_match_service_filtering(monkeypatch):
    # Mock api client to return raw /liveMatches json
    class MockClient:
        def get_live_matches(self):
            return {
                "data": [
                    {"match_id": "1", "match_status": "Live", "team_a": "A", "team_b": "B"},
                    {"match_id": "2", "match_status": "In Progress", "team_a": "C", "team_b": "D"},
                    {"match_id": "3", "match_status": "Completed", "team_a": "E", "team_b": "F"},
                    {"match_id": "4", "match_status": "Stumps", "team_a": "G", "team_b": "H"},
                    {"match_id": "5", "match_status": "Abandoned", "team_a": "I", "team_b": "J"},
                ]
            }
            
    service = LiveMatchService(api_client=MockClient())
    matches = service.get_live_matches()
    
    assert len(matches) == 2
    assert matches[0]["match_id"] == "1"
    assert matches[1]["match_id"] == "2"

def test_normalization():
    scorecard = {
        "status": True,
        "data": {
            "scorecard": {
                "1": {
                    "batsman": [{"name": "Sarthak Ranjan"}],
                    "bolwer": [{"name": "Lalit Yadav"}],
                    "team": {"score": 186, "wicket": 6, "over": "20", "inning": 1, "name": "NDS"},
                    "partnership": [{"run": 45, "ball": 27}]
                }
            }
        }
    }
    
    over_history = {
        "data": {
            "1": {
                "0": {
                    "overs": {"0": "1W", "1": "4", "2": "0"},
                    "team": {"over": 19, "runs": 5, "wkts": 1}
                },
                "1": {
                    "overs": {"0": "6", "1": "2"},
                    "team": {"over": 20, "runs": 8, "wkts": 0}
                }
            }
        }
    }
    
    state = normalize_live_data(scorecard, over_history, {})
    
    assert state["current_score"] == 186
    assert state["current_wickets"] == 6
    assert state["overs"] == "20"
    assert state["current_striker"] == "Sarthak Ranjan"
    assert state["current_bowler"] == "Lalit Yadav"
    assert state["partnership_runs"] == 45
    
    # recent_overs chronologically
    # over 19: 1W, 4, 0
    # over 20: 6, 2
    assert state["recent_overs"] == "1W 4 0 6 2"

def test_intelligence_service(monkeypatch):
    class MockClient:
        def get_scorecard(self, mid):
            return {"data": {"scorecard": {"1": {"team": {"score": 100, "wicket": 2, "over": "10.0"}}}}}
        def get_over_history(self, mid):
            return {"data": {}}
        def get_commentary(self, mid):
            return {"data": {}}
            
    intel = LiveIntelligenceService(api_client=MockClient())
    
    if intel.momentum_model is None or intel.win_model is None:
        pytest.skip("Models not found.")
        
    res = intel.get_live_intelligence("1234")
    
    assert "error" not in res
    assert res["status"] == "live"
    assert "momentum" in res
    assert "win_prediction" in res
    assert res["match"]["score"] == 100
