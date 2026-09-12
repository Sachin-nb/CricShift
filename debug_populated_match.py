import os
import json
from dotenv import load_dotenv
from backend.live.api_client import LiveAPIClient, APIClientError
from backend.live.match_service import LiveMatchService
from backend.live.intelligence import LiveIntelligenceService

load_dotenv()

def debug_populated_match():
    client = LiveAPIClient()
    match_service = LiveMatchService(client)
    intel_service = LiveIntelligenceService(client)
    
    print("\n" + "="*50)
    print("STEP 1 & 2: FETCH LIVE MATCHES")
    print("="*50)
    
    try:
        matches = match_service.get_live_matches()
        print(f"Number of live matches returned: {len(matches)}")
    except Exception as e:
        print(f"Failed to fetch matches: {e}")
        return
        
    if not matches:
        print("No matches currently marked as Live.")
        return

    populated_match_id = None
    matches_checked = []
    matches_no_data = []
    
    print("\n" + "="*50)
    print("STEP 3-5: SEARCH FOR POPULATED SCORECARD")
    print("="*50)
    
    for m in matches:
        mid = m.get("match_id")
        matches_checked.append(mid)
        print(f"Checking match {mid} ({m.get('team1')} vs {m.get('team2')})...")
        
        try:
            sc = client.get_scorecard(mid)
            if isinstance(sc, dict) and sc.get("status") is True:
                data = sc.get("data", {})
                if "scorecard" in data and len(data["scorecard"]) > 0:
                    populated_match_id = str(mid)
                    print(f"-> POPULATED DATA FOUND for {mid}!")
                    break
            else:
                matches_no_data.append(mid)
                print(f"-> No Data Found (status: {sc.get('status')})")
        except APIClientError as e:
            matches_no_data.append(mid)
            print(f"-> API Error: {e}")
        except Exception as e:
            print(f"-> Unknown Error: {e}")
            
    if not populated_match_id:
        print("\nNo currently available match contains usable scorecard data from the provider.")
        print(f"Matches checked: {matches_checked}")
        print(f"Matches with No Data: {matches_no_data}")
        return
        
    print("\n" + "="*50)
    print(f"STEP 6-7: VERIFY ALL ENDPOINTS FOR {populated_match_id}")
    print("="*50)
    
    try:
        oh = client.get_over_history(populated_match_id)
        print(f"OverHistory: status={oh.get('status', False)}")
        
        cm = client.get_commentary(populated_match_id)
        print(f"Commentary: status={cm.get('status', False)}")
    except Exception as e:
        print(f"Failed fetching detailed endpoints: {e}")
        
    print("\n" + "="*50)
    print(f"STEP 8-10: VERIFY BACKEND INTELLIGENCE")
    print("="*50)
    
    try:
        from fastapi.testclient import TestClient
        from backend.main import app
        from backend.dependencies import model_store
        
        # Explicitly load models so FastAPI routes work
        model_store.load_all()
        
        tc = TestClient(app)
        
        # 1. Get Intelligence
        resp = tc.get(f"/api/live/match/{populated_match_id}/intelligence")
        if resp.status_code == 200:
            intel_result = resp.json()
            match_state = intel_result.get("match", {})
            
            print("\n--- ML VERIFICATION ---")
            print(f"Score: {match_state.get('score')}/{match_state.get('wickets')} in {match_state.get('overs')} overs")
            
            mom = intel_result.get("momentum", {})
            print(f"Momentum: {mom.get('label')} (Prob: {mom.get('probabilities')})")
            
            win = intel_result.get("win_prediction", {})
            print(f"Win Probability: {win}")
        else:
            print(f"Intelligence Endpoint Error: {resp.status_code} {resp.text}")
            
        # Get live state directly for payloads
        state_resp = tc.get(f"/api/live/match/{populated_match_id}")
        if state_resp.status_code == 200:
            raw_state = state_resp.json()
            
            print("\n--- PLAYER VERIFICATION ---")
            print(f"CURRENT BATTERS (Striker): {raw_state.get('current_striker')}")
            print(f"CURRENT BOWLERS: {raw_state.get('current_bowler')}")
            
            # Map state to base schemas
            # Note: current_over must be int for Simulation/Explain schemas, but float for Recommendation
            c_over_val = raw_state.get("overs", 0.0)
            c_over_int = int(float(c_over_val)) if c_over_val else 0
            
            base_schema = {
                "season": "2024",
                "venue": raw_state.get("venue") or "Unknown",
                "batting_team": raw_state.get("batting_team") or "Unknown",
                "bowling_team": raw_state.get("bowling_team") or "Unknown",
                "innings": raw_state.get("innings", 1),
                "current_over": c_over_int,
                "current_score": raw_state.get("current_score", 0),
                "current_wickets": raw_state.get("current_wickets", 0),
                "target": raw_state.get("target", 0),
                "batter_name": raw_state.get("current_striker") or "Unknown",
                "bowler_name": raw_state.get("current_bowler") or "Unknown"
            }
            
            print("\n--- EXPLAINABILITY (SHAP) ---")
            exp_req = {"model": "both", **base_schema}
            exp_resp = tc.post("/api/explain", json=exp_req)
            if exp_resp.status_code == 200:
                print("Explainability Status: SUCCESS")
                er = exp_resp.json()
                print(f"Top Features: {er.get('top_features')}")
                mom_contribs = er.get("feature_contributions", {}).get("momentum", [])
                if mom_contribs:
                    print("Top Momentum Contributor: ", mom_contribs[0])
            else:
                print(f"Explainability Status: FAILED ({exp_resp.status_code} - {exp_resp.text})")
                
            print("\n--- PLAYER RECOMMENDATION ---")
            rec_req = {
                "batting_team": base_schema["batting_team"],
                "bowling_team": base_schema["bowling_team"],
                "venue": base_schema["venue"],
                "current_score": base_schema["current_score"],
                "current_wickets": base_schema["current_wickets"],
                "current_over": float(c_over_val) if c_over_val else 0.0,
                "required_run_rate": 8.0,
                "pressure_index": 5.0,
                "momentum_score": 2.0,
                "current_batter": base_schema["batter_name"],
                "current_bowler": base_schema["bowler_name"],
                "dismissed_batters": [],
                "top_n": 2
            }
            rec_resp = tc.post("/api/recommend/player", json=rec_req)
            if rec_resp.status_code == 200:
                print("Recommendation Status: SUCCESS")
                rr = rec_resp.json()
                recs = rr.get("recommendations", [])
                if recs:
                    print(f"Top Recommended Player: {recs[0].get('Player')} - Reason: {recs[0].get('Reason')}")
                else:
                    print("No recommendations generated (likely missing historical data).")
            else:
                print(f"Recommendation Status: FAILED ({rec_resp.status_code} - {rec_resp.text})")
                
            print("\n--- WHAT-IF SIMULATION ---")
            # The simulator expects EXACT feature column names for modifications
            sim_req = {
                **base_schema,
                "modifications": {"Current_Score": base_schema["current_score"] + 10},
                "scenario_name": "+10 runs"
            }
            sim_resp = tc.post("/api/simulate", json=sim_req)
            if sim_resp.status_code == 200:
                print("Simulation (+10 runs) Status: SUCCESS")
                sim_res = sim_resp.json()
                print(f"Original Win: {sim_res.get('original', {}).get('win_probability_pct', 0.0)}%")
                print(f"Simulated Win: {sim_res.get('modified', {}).get('win_probability_pct', 0.0)}%")
                delta = sim_res.get('delta', {}).get('win_probability_delta', 0.0)
                print(f"Difference: {delta}%")
            else:
                print(f"Simulation Status: FAILED ({sim_resp.status_code} - {sim_resp.text})")
                
            # Replace batter simulation
            print("\n--- WHAT-IF SIMULATION (Player Replacement) ---")
            sim_req_rep = {
                **base_schema,
                "modifications": {"replace_batter": "Virat Kohli"},
                "scenario_name": "Bring in Kohli"
            }
            sim_resp_rep = tc.post("/api/simulate", json=sim_req_rep)
            if sim_resp_rep.status_code == 200:
                print("Simulation (Replace Batter) Status: SUCCESS")
                sim_res_rep = sim_resp_rep.json()
                print(f"Simulated Win (with Kohli): {sim_res_rep.get('modified', {}).get('win_probability_pct', 0.0)}%")
                delta_rep = sim_res_rep.get('delta', {}).get('win_probability_delta', 0.0)
                print(f"Difference: {delta_rep}%")
            else:
                print(f"Simulation (Replace Batter) Status: FAILED ({sim_resp_rep.status_code} - {sim_resp_rep.text})")
                
        else:
            print("Failed to get match state for payload.")
            
    except Exception as e:
        print(f"Backend Intelligence Error: {e}")

if __name__ == "__main__":
    debug_populated_match()
