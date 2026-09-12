import pytest
import pandas as pd
from backend.live.feature_adapter import LiveFeatureAdapter
from backend.live.matcher import normalize_name, match_name
from backend.live import db

def test_cricket_over_parsing():
    adapter = LiveFeatureAdapter()
    
    # 19.3 -> 19 overs, 3 balls -> 117 total balls
    o, b, t = adapter.parse_cricket_overs(19.3)
    assert o == 19
    assert b == 3
    assert t == 117
    
    # 0.1 -> 0 overs, 1 ball -> 1 total ball
    o, b, t = adapter.parse_cricket_overs(0.1)
    assert o == 0
    assert b == 1
    assert t == 1
    
    # 10.5 -> 10 overs, 5 balls -> 65 total balls
    o, b, t = adapter.parse_cricket_overs(10.5)
    assert o == 10
    assert b == 5
    assert t == 65
    
    # Weird API decimal like 19.6 (just before rolling to 20.0) -> 120 balls
    o, b, t = adapter.parse_cricket_overs(19.6)
    assert o == 19
    assert b == 6
    assert t == 120

def test_name_matching():
    valid_names = ["MS Dhoni", "Virat Kohli", "Rohit Sharma", "Royal Challengers Bangalore"]
    
    # Exact Match
    assert match_name("MS Dhoni", valid_names, "player") == "MS Dhoni"
    
    # Normalized Match
    assert match_name("M.S. Dhoni", valid_names, "player") == "MS Dhoni"
    assert match_name("M S Dhoni", valid_names, "player") == "MS Dhoni"
    
    # Fuzzy Match (conservative, so a small typo passes)
    assert match_name("Virat Kholi", valid_names, "player") == "Virat Kohli"
    
    # Complete miss returns None
    assert match_name("Unknown Rookie", valid_names, "player") is None

def test_live_feature_adapter():
    adapter = LiveFeatureAdapter()
    
    # Mock realistic live API payload for NRK vs VKK
    mock_payload = {
        "season": "2024",
        "venue": "Indian Cement Company Ground, Tirunelveli",
        "team1": "Nellai Royal Kings",
        "team2": "Lyca Kovai Kings", # Deliberate mismatch to VKK to test matcher
        "batting_team": "Nellai Royal Kings",
        "score": 158,
        "wickets": 8,
        "overs": 19.3,
        "target": 163,
        "current_striker": "NS Harish",
        "current_bowler": "G Kishoor",
        "recent_overs": "6 6 W 0 1 2 4 1 W",
        "partnership_runs": 12,
        "partnership_balls": 5
    }
    
    df = adapter.process_live_payload(mock_payload)
    
    assert len(df) == 1, "Should produce exactly 1 row"
    
    # Ensure correct columns exist
    momentum_df = adapter.get_momentum_features(df)
    assert len(momentum_df.columns) == len(adapter.momentum_features), "Momentum feature count mismatch"
    assert list(momentum_df.columns) == adapter.momentum_features, "Momentum feature order mismatch"
    
    win_df = adapter.get_win_features(df)
    assert len(win_df.columns) == len(adapter.win_features), "Win prediction feature count mismatch"
    assert list(win_df.columns) == adapter.win_features, "Win prediction feature order mismatch"

    # Verify calculated math
    assert df.iloc[0]["Current_Over"] == 19
    assert df.iloc[0]["Current_Ball"] == 3
    
    # recent_overs string ending in W -> Wicket_last_6_balls should have 1 Wicket, but earlier is another W.
    # The last 6 of "6 6 W 0 1 2 4 1 W" are "0 1 2 4 1 W". That's 1 wicket, 1 boundary, 1 dot ball.
    assert df.iloc[0]["Wickets_Last_6_Balls"] == 1
    assert df.iloc[0]["Dot_Balls_Last_6_Balls"] == 1
    assert df.iloc[0]["Boundaries_Last_6_Balls"] == 1
    
    # Unknown players (NS Harish, G Kishoor) should have their stats cleanly filled with 0
    assert df.iloc[0]["Batter_Career_Average"] == 0.0
    assert df.iloc[0]["Bowler_Economy"] == 0.0

def test_model_compatibility():
    # Load actual models and ensure they can infer on the adapter's output without crashing
    import pickle
    from pathlib import Path
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    momentum_model_path = BASE_DIR / "models" / "momentum" / "best_model.pkl"
    win_model_path = BASE_DIR / "models" / "win_prediction" / "best_model.pkl"
    
    if not momentum_model_path.exists() or not win_model_path.exists():
        pytest.skip("Models not found, skipping compatibility test.")
        
    with open(momentum_model_path, "rb") as f:
        momentum_model = pickle.load(f)
        
    with open(win_model_path, "rb") as f:
        win_model = pickle.load(f)
        
    adapter = LiveFeatureAdapter()
    mock_payload = {
        "season": "2024",
        "venue": "Eden Gardens",
        "batting_team": "Kolkata Knight Riders",
        "team2": "Mumbai Indians",
        "score": 120,
        "wickets": 3,
        "overs": 14.5,
        "target": 180,
        "current_striker": "AD Russell",
        "current_bowler": "JJ Bumrah",
        "recent_overs": "0 1 1 6 4 0"
    }
    
    df = adapter.process_live_payload(mock_payload)
    
    mom_df = adapter.get_momentum_features(df)
    win_df = adapter.get_win_features(df)
    
    # Predict
    mom_pred = momentum_model.predict(mom_df)
    win_pred = win_model.predict_proba(win_df)
    
    assert len(mom_pred) == 1
    assert len(win_pred) == 1
