import os
import json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# Project root = this script's own directory (portable across machines).
PROJECT_ROOT = Path(__file__).resolve().parent

def test_historical_upload():
    print("--- 1. HISTORICAL BACKEND VERIFICATION ---")
    csv_path = str(PROJECT_ROOT / "data" / "uploads" / "uploaded_match.csv")
    
    if not os.path.exists(csv_path):
        print(f"FAIL: Dataset not found at {csv_path}")
        return False
        
    print(f"Testing POST /api/historical/upload with {os.path.basename(csv_path)}...")
    
    with client as c:
        with open(csv_path, "rb") as f:
            response = c.post("/api/historical/upload", files={"file": ("uploaded_match.csv", f, "text/csv")})
            
        if response.status_code != 200:
            print(f"FAIL: HTTP {response.status_code}")
            print(response.text)
            return False
            
        data = response.json()
        print("PASS: HTTP 200 OK")
        
        keys = data.keys()
        expected = ["analysis_id", "match_info", "timeline", "turning_points", "latest_state"]
        
        print(f"Keys present: {list(keys)}")
        for e in expected:
            if e not in keys:
                print(f"FAIL: Missing key '{e}' in response")
                return False
                
        print(f"PASS: Timeline points generated: {len(data['timeline'])}")
        print(f"PASS: Turning points detected: {len(data['turning_points'])}")
        
        if len(data['timeline']) > 0:
            p = data['timeline'][0]
            print("First timeline point keys:", list(p.keys()))
            if 'momentum_probabilities' in p and 'win_probability' in p:
                print("PASS: Momentum and Win Probabilities are present in timeline.")
            else:
                print("FAIL: Missing Momentum/Win Prob in timeline point.")
                return False
                
        return True

def test_phase_3c_endpoints():
    print("\n--- 2. PHASE 3C VERIFICATION ---")
    
    state = {
        "season": "2024",
        "venue": "Wankhede Stadium, Mumbai",
        "batting_team": "Mumbai Indians",
        "bowling_team": "Chennai Super Kings",
        "innings": 1,
        "current_over": 15,
        "current_ball": 6,
        "current_score": 140,
        "current_wickets": 4,
        "target": 0,
        "batter_name": "Suryakumar Yadav",
        "bowler_name": "Ravindra Jadeja",
        "runs_last_6_balls": 12,
        "runs_last_12_balls": 20,
        "runs_last_18_balls": 30,
        "runs_last_30_balls": 45,
        "wickets_last_6_balls": 0,
        "wickets_last_12_balls": 1,
        "boundaries_last_6_balls": 2,
        "boundaries_last_12_balls": 3,
        "dot_balls_last_6_balls": 1,
        "dot_balls_last_12_balls": 3
    }
    
    with client as c:
        res_explain = c.post("/api/explain", json=state)
        if res_explain.status_code == 200:
            print("PASS: POST /api/explain -> 200 OK")
            print("  Explain data length/type:", type(res_explain.json()))
        else:
            print("FAIL: POST /api/explain", res_explain.status_code, res_explain.text)
            
        res_rec = c.post("/api/recommend/player", json={
            "batting_team": state["batting_team"],
            "bowling_team": state["bowling_team"],
            "venue": state["venue"],
            "current_score": state["current_score"],
            "current_wickets": state["current_wickets"],
            "current_over": state["current_over"],
            "current_batter": state["batter_name"],
            "current_bowler": state["bowler_name"]
        })
        if res_rec.status_code == 200:
            print("PASS: POST /api/recommend/player -> 200 OK")
            recs = res_rec.json().get('recommendations', [])
            if recs:
                print("  Top recommendation:", recs[0].get('Player'))
            else:
                print("  Warning: No recommendations returned")
        else:
            print("FAIL: POST /api/recommend/player", res_rec.status_code, res_rec.text)
            
        sim_payload = {**state, "modifications": {"current_score": state["current_score"] + 10}, "scenario_name": "wicket"}
        res_sim = c.post("/api/simulate", json=sim_payload)
        if res_sim.status_code == 200:
            print("PASS: POST /api/simulate -> 200 OK")
            print("  Win probability delta:", res_sim.json().get('delta', {}).get('win_probability', {}).get(state['batting_team']))
        else:
            print("FAIL: POST /api/simulate", res_sim.status_code, res_sim.text)

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')
    
    hist_ok = test_historical_upload()
    test_phase_3c_endpoints()
