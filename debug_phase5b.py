import os
from dotenv import load_dotenv
from backend.live.api_client import LiveAPIClient

load_dotenv()

def print_separator(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

def debug_live_matches():
    client = LiveAPIClient()
    
    # Hide the key in logs manually just to be safe
    print(f"Host: {client.host}")
    print(f"Key loaded: {'YES' if client.api_key else 'NO'}")
    
    print_separator("STEP 2: DIRECT /liveMatches TEST")
    try:
        matches = client.get_live_matches()
        print("Status: 200 OK (Since no exception raised)")
        print(f"Response type: {type(matches)}")
        
        if isinstance(matches, dict):
            print(f"Top level keys: {list(matches.keys())}")
            data_arr = matches.get("data", matches.get("matches", []))
            if isinstance(data_arr, dict):
                data_arr = list(data_arr.values())
        elif isinstance(matches, list):
            data_arr = matches
        else:
            data_arr = []
            
        print(f"Number of matches found: {len(data_arr)}")
        
        if len(data_arr) > 0:
            m = data_arr[0]
            print(f"\nFirst match ACTUAL keys: {list(m.keys())}")
            print("\nFirst match full dump (safe strings only):")
            for k, v in m.items():
                if isinstance(v, (str, int, float, bool)):
                    print(f"  {k}: {v}")
                else:
                    print(f"  {k}: <{type(v).__name__}>")
                    
    except Exception as e:
        print(f"API Error: {e}")

def debug_match_4838():
    client = LiveAPIClient()
    match_id = "4838"
    print_separator(f"STEP 4: DIRECT MATCH {match_id} TEST")
    
    try:
        sc = client.get_scorecard(match_id)
        print("Scorecard: 200 OK")
        if isinstance(sc, dict) and "data" in sc:
            print("Scorecard returned valid data wrapper.")
    except Exception as e:
        print(f"Scorecard Error: {e}")
        
    try:
        oh = client.get_over_history(match_id)
        print("OverHistory: 200 OK")
        if isinstance(oh, dict) and "data" in oh:
            print("OverHistory returned valid data wrapper.")
    except Exception as e:
        print(f"OverHistory Error: {e}")
        
    try:
        cm = client.get_commentary(match_id)
        print("Commentary: 200 OK")
        if isinstance(cm, dict) and "data" in cm:
            print("Commentary returned valid data wrapper.")
    except Exception as e:
        print(f"Commentary Error: {e}")

if __name__ == "__main__":
    debug_live_matches()
    debug_match_4838()
