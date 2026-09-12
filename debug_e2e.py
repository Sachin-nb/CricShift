import os
import json
from dotenv import load_dotenv
from backend.live.intelligence import LiveIntelligenceService

load_dotenv()

def debug_e2e_pipeline():
    match_id = "14095" # The match we found in step 2
    print(f"\n{'='*50}\nSTEP 6: E2E TEST (Match {match_id})\n{'='*50}")
    
    try:
        service = LiveIntelligenceService()
        result = service.get_live_intelligence(match_id)
        
        print(f"Status: {result.get('status')}")
        if "error" in result:
            print(f"ERROR: {result.get('error')} - {result.get('details')}")
        else:
            print("\nSUCCESS! Pipeline executed completely.")
            print(f"Batting Team: {result.get('match', {}).get('batting_team')}")
            print(f"Score: {result.get('match', {}).get('score')} / {result.get('match', {}).get('wickets')}")
            print(f"Momentum: {result.get('momentum', {}).get('label')}")
            print(f"Win Probs: {result.get('win_prediction')}")
            
    except Exception as e:
        print(f"Exception during E2E: {e}")

if __name__ == "__main__":
    debug_e2e_pipeline()
