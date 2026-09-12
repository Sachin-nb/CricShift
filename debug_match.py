import os
from dotenv import load_dotenv
from backend.live.api_client import LiveAPIClient

load_dotenv()

def print_separator(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

def inspect_json(name, data):
    print(f"\n--- {name} Top Level ---")
    if isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        print(f"Status: {data.get('status')} | Msg: {data.get('msg')}")
        if "data" in data:
            d = data["data"]
            if isinstance(d, dict):
                print(f"Data Keys: {list(d.keys())}")
                if "scorecard" in d and isinstance(d["scorecard"], dict):
                    print(f"Scorecard Keys: {list(d['scorecard'].keys())}")
                    # Look deeper into scorecard
                    sc = d["scorecard"]
                    if sc and isinstance(sc, dict):
                        first_sc = list(sc.values())[0] if len(sc) > 0 else {}
                        if isinstance(first_sc, dict):
                            print(f"First Innings Keys: {list(first_sc.keys())}")
                elif len(d.keys()) > 0:
                    # Possibly overHistory where keys are "1", "2"
                    first_k = list(d.keys())[0]
                    first_v = d[first_k]
                    if isinstance(first_v, dict):
                        print(f"First element '{first_k}' keys: {list(first_v.keys())}")
                        # For overHistory, might have "0", "1" for overs
                        if len(first_v) > 0:
                            inner_k = list(first_v.keys())[0]
                            inner_v = first_v[inner_k]
                            if isinstance(inner_v, dict):
                                print(f"Inner '{inner_k}' keys: {list(inner_v.keys())}")
                                if "team" in inner_v:
                                    print(f"Team obj: {inner_v['team']}")
            elif isinstance(d, list):
                print(f"Data is list of len: {len(d)}")
                if len(d) > 0 and isinstance(d[0], dict):
                    print(f"First list element keys: {list(d[0].keys())}")
    else:
        print(f"Response is not a dict: {type(data)}")

def debug_match_endpoints():
    client = LiveAPIClient()
    match_id = "14095"
    
    print_separator(f"DIRECT MATCH {match_id} ENDPOINT TEST")
    
    try:
        sc = client.get_scorecard(match_id)
        inspect_json("SCORECARD", sc)
    except Exception as e:
        print(f"Scorecard Error: {e}")
        
    try:
        oh = client.get_over_history(match_id)
        inspect_json("OVER HISTORY", oh)
    except Exception as e:
        print(f"OverHistory Error: {e}")
        
    try:
        cm = client.get_commentary(match_id)
        inspect_json("COMMENTARY", cm)
    except Exception as e:
        print(f"Commentary Error: {e}")

if __name__ == "__main__":
    debug_match_endpoints()
