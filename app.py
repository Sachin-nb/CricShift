"""
Cricket Momentum Shift Detector - Flask Application
=====================================================
Main entry point for the web application. Provides:
  - Dashboard page serving the analytics UI
  - REST API endpoints for ball-by-ball data retrieval
  - File upload endpoint for custom CSV datasets
  - Analytics pipeline orchestration

Architecture:
  Browser  <──>  Flask Routes  <──>  Engine Pipeline  <──>  CSV Data
"""

import os
import json
import math
import uuid
from flask import Flask, render_template, jsonify, request, send_from_directory
import pandas as pd
import numpy as np

# Engine imports
from engine.data_loader import DataLoader
from engine.feature_engine import FeatureEngine
from engine.momentum_model import MomentumModel
from engine.win_probability import WinProbabilityEngine
from engine.shift_detector import ShiftDetector
import config

# ── Flask App Setup ────────────────────────────────────────────────
app = Flask(__name__)
# Max upload size read from env var (default 100 MB).
# Override with MAX_UPLOAD_MB=50 in .env for smaller cap.
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_UPLOAD_MB", "100")) * 1024 * 1024
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.errorhandler(413)
def too_large(e):
    """Return JSON error for files that exceed the upload limit."""
    return jsonify({"error": "File too large. Maximum upload size is 100 MB."}), 413

# ── Global State ───────────────────────────────────────────────────
# Stores the processed match data for the current session
_current_match = {
    "loaded": False,
    "filepath": None,
    "raw_data": None,
    "innings1_data": None,
    "innings2_data": None,
    "teams": None,
    "target": 0,
    "match_summary": None,
}


def _safe_value(val):
    """Convert NaN/Inf to None for JSON serialization."""
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val


def _process_match(filepath: str):
    """
    Run the full analytics pipeline on a match dataset.

    Steps:
        1. Load and validate CSV data
        2. Compute features for both innings
        3. Calculate momentum index
        4. Compute win probabilities
        5. Detect momentum shifts

    Args:
        filepath: Path to CSV file.
    """
    global _current_match

    # Step 1: Load data
    loader = DataLoader(filepath)
    raw_df = loader.load()
    teams = loader.get_teams()
    match_summary = loader.get_match_summary()

    # Step 2-5: Process each innings
    innings1_df = loader.get_innings_data(1)
    innings1_total = int(innings1_df["total_runs"].sum()) if len(innings1_df) > 0 else 0
    target = innings1_total + 1

    processed_innings = {}
    for innings_num in [1, 2]:
        inn_df = loader.get_innings_data(innings_num)
        if len(inn_df) == 0:
            continue

        # Feature engineering
        feat_engine = FeatureEngine(
            target_score=target if innings_num == 2 else 0
        )
        inn_df = feat_engine.compute_features(inn_df, innings=innings_num)

        # Momentum model
        momentum_model = MomentumModel()
        inn_df = momentum_model.calculate(inn_df, innings=innings_num)

        # Win probability
        win_prob_engine = WinProbabilityEngine(
            target_score=target if innings_num == 2 else 0
        )
        inn_df = win_prob_engine.calculate(inn_df, innings=innings_num)

        # Shift detection
        shift_detector = ShiftDetector()
        inn_df = shift_detector.detect(inn_df)

        processed_innings[innings_num] = inn_df

    _current_match = {
        "loaded": True,
        "filepath": filepath,
        "raw_data": raw_df,
        "innings1_data": processed_innings.get(1),
        "innings2_data": processed_innings.get(2),
        "teams": teams,
        "target": target,
        "match_summary": match_summary,
    }


def _ball_to_dict(row: pd.Series) -> dict:
    """Convert a ball DataFrame row to a JSON-serializable dictionary."""
    return {
        "innings": int(row.get("innings", 0)),
        "over": int(row.get("over", 0)),
        "ball": int(row.get("ball", 0)),
        "over_exact": _safe_value(float(row.get("over_exact", 0))),
        "ball_number": int(row.get("ball_number", 0)),
        "batting_team": str(row.get("batting_team", "")),
        "bowling_team": str(row.get("bowling_team", "")),
        "batsman": str(row.get("batsman", "")),
        "bowler": str(row.get("bowler", "")),
        "runs_off_bat": int(row.get("runs_off_bat", 0)),
        "extras": int(row.get("extras", 0)),
        "total_runs": int(row.get("total_runs", 0)),
        "is_wicket": int(row.get("is_wicket", 0)),
        "dismissal_kind": str(row.get("dismissal_kind", "")),
        "player_dismissed": str(row.get("player_dismissed", "")),
        "cumulative_runs": int(row.get("cumulative_runs", 0)),
        "cumulative_wickets": int(row.get("cumulative_wickets", 0)),
        "is_boundary": int(row.get("is_boundary", 0)),
        "is_dot": int(row.get("is_dot", 0)),
        # Features
        "current_run_rate": _safe_value(float(row.get("current_run_rate", 0))),
        "required_run_rate": _safe_value(float(row.get("required_run_rate", 0))),
        "runs_last_over": _safe_value(float(row.get("runs_last_over", 0))),
        "runs_last_5_overs": _safe_value(float(row.get("runs_last_5_overs", 0))),
        "wickets_last_n": _safe_value(float(row.get("wickets_last_n", 0))),
        "dot_ball_pct": _safe_value(float(row.get("dot_ball_pct", 0))),
        "boundary_freq": _safe_value(float(row.get("boundary_freq", 0))),
        "pressure_index": _safe_value(float(row.get("pressure_index", 0))),
        "run_rate_acceleration": _safe_value(float(row.get("run_rate_acceleration", 0))),
        # Momentum
        "momentum_index": _safe_value(float(row.get("momentum_index", 0))),
        "momentum_change": _safe_value(float(row.get("momentum_change", 0))),
        # Win probability
        "win_prob_batting": _safe_value(float(row.get("win_prob_batting", 50))),
        "win_prob_bowling": _safe_value(float(row.get("win_prob_bowling", 50))),
        # Shifts
        "is_shift": bool(row.get("is_shift", False)),
        "shift_severity": str(row.get("shift_severity", "")),
        "shift_description": str(row.get("shift_description", "")),
    }


# ══════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/")
def dashboard():
    """Serve the main dashboard page."""
    return render_template("index.html")


@app.route("/api/load-default", methods=["POST"])
def load_default_match():
    """Load the sample match dataset."""
    sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_match.csv")
    if not os.path.exists(sample_path):
        return jsonify({"error": "Sample dataset not found. Run generate_sample_data.py first."}), 404

    try:
        _process_match(sample_path)
        return jsonify({
            "success": True,
            "message": "Sample match loaded successfully",
            "match_summary": _current_match["match_summary"],
            "teams": _current_match["teams"],
            "target": _current_match["target"],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload", methods=["POST"])
def upload_match():
    """Upload a custom CSV dataset."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only CSV files are supported"}), 400

    unique_id = uuid.uuid4().hex[:8]
    filename = f"match_{unique_id}.csv"
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)

    try:
        _process_match(filepath)
        return jsonify({
            "success": True,
            "message": "Match data uploaded and processed",
            "match_id": unique_id,
            "match_summary": _current_match["match_summary"],
            "teams": _current_match["teams"],
            "target": _current_match["target"],
        })
    except ValueError as e:
        return jsonify({"error": f"Data format issue: {str(e)}"}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Processing error: {str(e)}"}), 500


@app.route("/api/match-info")
def match_info():
    """Get current match metadata."""
    if not _current_match["loaded"]:
        return jsonify({"error": "No match loaded"}), 400

    return jsonify({
        "teams": _current_match["teams"],
        "target": _current_match["target"],
        "match_summary": _current_match["match_summary"],
    })


@app.route("/api/innings/<int:innings_num>/ball/<int:ball_index>")
def get_ball(innings_num, ball_index):
    """
    Get computed data for a specific ball in an innings.

    Args:
        innings_num: 1 or 2
        ball_index: 0-indexed ball position in the innings

    Returns:
        JSON with ball data and all computed features.
    """
    if not _current_match["loaded"]:
        return jsonify({"error": "No match loaded"}), 400

    key = f"innings{innings_num}_data"
    df = _current_match.get(key)
    if df is None:
        return jsonify({"error": f"Innings {innings_num} data not available"}), 400

    if ball_index < 0 or ball_index >= len(df):
        return jsonify({"error": f"Ball index {ball_index} out of range (0-{len(df)-1})"}), 400

    row = df.iloc[ball_index]
    return jsonify(_ball_to_dict(row))


@app.route("/api/innings/<int:innings_num>/balls")
def get_all_balls(innings_num):
    """
    Get all balls for an innings with computed features.
    Supports optional range query params: ?start=0&end=30

    Returns:
        JSON array of ball data.
    """
    if not _current_match["loaded"]:
        return jsonify({"error": "No match loaded"}), 400

    key = f"innings{innings_num}_data"
    df = _current_match.get(key)
    if df is None:
        return jsonify({"error": f"Innings {innings_num} data not available"}), 400

    start = request.args.get("start", 0, type=int)
    end = request.args.get("end", len(df), type=int)
    end = min(end, len(df))

    balls = []
    for i in range(start, end):
        balls.append(_ball_to_dict(df.iloc[i]))

    return jsonify({
        "innings": innings_num,
        "total_balls": len(df),
        "range": {"start": start, "end": end},
        "balls": balls,
    })


@app.route("/api/innings/<int:innings_num>/state/<int:ball_index>")
def get_match_state(innings_num, ball_index):
    """
    Get the complete match state at a specific ball position.
    Used by the frontend to render the full dashboard view.

    Returns:
        JSON with current ball, cumulative stats, graphs data,
        turning points, and feed history.
    """
    if not _current_match["loaded"]:
        return jsonify({"error": "No match loaded"}), 400

    key = f"innings{innings_num}_data"
    df = _current_match.get(key)
    if df is None:
        return jsonify({"error": f"Innings {innings_num} data not available"}), 400

    ball_index = min(max(0, ball_index), len(df) - 1)

    current_ball = _ball_to_dict(df.iloc[ball_index])

    # Momentum graph data (up to current ball)
    momentum_data = {
        "overs": [_safe_value(float(df.iloc[i]["over_exact"])) for i in range(ball_index + 1)],
        "momentum": [_safe_value(float(df.iloc[i]["momentum_index"])) for i in range(ball_index + 1)],
        "ball_numbers": list(range(1, ball_index + 2)),
    }

    # Win probability graph data
    win_prob_data = {
        "overs": momentum_data["overs"],
        "batting_prob": [_safe_value(float(df.iloc[i]["win_prob_batting"])) for i in range(ball_index + 1)],
        "bowling_prob": [_safe_value(float(df.iloc[i]["win_prob_bowling"])) for i in range(ball_index + 1)],
        "ball_numbers": momentum_data["ball_numbers"],
    }

    # Ball feed (last N balls)
    feed_start = max(0, ball_index - config.BALL_FEED_MAX_DISPLAY + 1)
    feed_balls = []
    for i in range(feed_start, ball_index + 1):
        feed_balls.append(_ball_to_dict(df.iloc[i]))

    # Turning points up to current ball
    shift_detector = ShiftDetector()
    current_df = df.iloc[:ball_index + 1]
    turning_points = shift_detector.get_turning_points(current_df)

    # Stats cards
    stats = {
        "runs_last_5_overs": _safe_value(float(current_ball.get("runs_last_5_overs", 0))),
        "dot_ball_pct": _safe_value(float(current_ball.get("dot_ball_pct", 0))),
        "pressure_index": _safe_value(float(current_ball.get("pressure_index", 0))),
        "momentum_score": _safe_value(float(current_ball.get("momentum_index", 0))),
        "boundary_freq": _safe_value(float(current_ball.get("boundary_freq", 0))),
        "run_rate_acceleration": _safe_value(float(current_ball.get("run_rate_acceleration", 0))),
    }

    # Innings 1 summary (for header display during innings 2)
    innings1_summary = None
    if _current_match["innings1_data"] is not None:
        inn1 = _current_match["innings1_data"]
        innings1_summary = {
            "total_runs": int(inn1["total_runs"].sum()),
            "total_wickets": int(inn1["is_wicket"].sum()),
            "total_overs": f"{int(inn1['over'].iloc[-1])}.{int(inn1['ball'].iloc[-1])}",
        }

    return jsonify({
        "current_ball": current_ball,
        "ball_index": ball_index,
        "total_balls": len(df),
        "innings": innings_num,
        "teams": _current_match["teams"],
        "target": _current_match["target"],
        "innings1_summary": innings1_summary,
        "momentum_data": momentum_data,
        "win_prob_data": win_prob_data,
        "feed": feed_balls,
        "turning_points": turning_points,
        "stats": stats,
    })


@app.route("/api/innings/<int:innings_num>/summary")
def innings_summary(innings_num):
    """Get summary statistics for an entire innings."""
    if not _current_match["loaded"]:
        return jsonify({"error": "No match loaded"}), 400

    key = f"innings{innings_num}_data"
    df = _current_match.get(key)
    if df is None:
        return jsonify({"error": f"Innings {innings_num} data not available"}), 400

    summary = {
        "total_runs": int(df["total_runs"].sum()),
        "total_wickets": int(df["is_wicket"].sum()),
        "total_balls": len(df),
        "boundaries_4": int((df["runs_off_bat"] == 4).sum()),
        "boundaries_6": int((df["runs_off_bat"] == 6).sum()),
        "dot_balls": int(df["is_dot"].sum()),
        "extras": int(df["extras"].sum()),
        "highest_momentum": _safe_value(float(df["momentum_index"].max())),
        "lowest_momentum": _safe_value(float(df["momentum_index"].min())),
        "shifts_detected": int(df["is_shift"].sum()),
    }
    return jsonify(summary)


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Read runtime settings from environment variables instead of hardcoding.
    flask_debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    flask_port  = int(os.environ.get("FLASK_PORT", "5000"))
    max_upload  = int(os.environ.get("MAX_UPLOAD_MB", "100")) * 1024 * 1024
    app.config["MAX_CONTENT_LENGTH"] = max_upload

    # Auto-load sample data on startup if available
    sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_match.csv")
    if os.path.exists(sample_path):
        print("⏳ Pre-loading sample match data...")
        _process_match(sample_path)
        print("✓ Sample match loaded successfully")
        if _current_match["match_summary"]:
            summary = _current_match["match_summary"]
            teams = _current_match["teams"]
            print(f"  {teams['team1']} vs {teams['team2']}")
            print(f"  Innings 1: {summary['innings1_total']}/{summary['innings1_wickets']} ({summary['innings1_overs']} ov)")
            print(f"  Innings 2: {summary['innings2_total']}/{summary['innings2_wickets']} ({summary['innings2_overs']} ov)")

    print("\n🏏 Starting Momentum Shift Detector...")
    print(f"   Dashboard: http://localhost:{flask_port}\n")
    # NOTE: debug=True is NOT suitable for production. Use FLASK_DEBUG=true only locally.
    app.run(debug=flask_debug, host="0.0.0.0", port=flask_port)
