"""
Historical route — POST /api/historical/upload
Phase 5C: Processes a historical match dataset and returns a full timeline analysis.
"""

import io
import logging
from typing import Any, Dict, List
from fastapi import APIRouter, File, UploadFile, HTTPException
import pandas as pd
import numpy as np

from backend.dependencies import model_store
from backend.config import DEFAULT_SEASON
from backend.live.turning_points import build_turning_point_reason
from backend.live.activity_db import log_historical_analysis
from feature_engineering.feature_utils import (
    calculate_rolling_features,
    calculate_momentum_scores,
    calculate_partnership_features
)

logger = logging.getLogger("backend.historical")
router = APIRouter(tags=["Historical"])

# Max CSV upload size: 20 MB (configurable via env var MAX_HISTORICAL_MB)
import os
_MAX_BYTES = int(os.getenv("MAX_HISTORICAL_MB", "20")) * 1024 * 1024


def _parse_raw_cricsheet(lines: List[str]) -> tuple[pd.DataFrame, dict]:
    """Parse raw Cricsheet CSV format (starting with version, info, and ball rows)."""
    meta = {"teams": []}
    balls = []
    
    for line in lines:
        if not line.strip():
            continue
        parts = [p.strip().strip('"') for p in line.split(",")]
        if not parts:
            continue
        
        row_type = parts[0].lower()
        if row_type == "info" and len(parts) >= 3:
            k = parts[1].lower()
            v = parts[2]
            if k == "team":
                meta["teams"].append(v)
            elif k in ("winner", "venue", "season", "city", "event", "player_of_match"):
                meta[k] = v
            elif k == "winner_runs":
                meta["winner_runs"] = v
            elif k == "winner_wickets":
                meta["winner_wickets"] = v
        elif row_type == "ball" and len(parts) >= 8:
            # Format: ball, innings, over.ball, batting_team, batter, non_striker, bowler, runs_off_bat, extras, [wicket_type, player_dismissed]
            innings = int(parts[1]) if parts[1].isdigit() else 1
            over_ball_raw = float(parts[2]) if parts[2].replace(".", "", 1).isdigit() else 0.1
            over_num = int(over_ball_raw) + 1
            ball_num = int(round((over_ball_raw % 1) * 10))
            batting_team = parts[3]
            batter = parts[4]
            non_striker = parts[5] if len(parts) > 5 else ""
            bowler = parts[6] if len(parts) > 6 else ""
            runs_bat = int(parts[7]) if len(parts) > 7 and parts[7].isdigit() else 0
            extras = int(parts[8]) if len(parts) > 8 and parts[8].isdigit() else 0
            total_runs = runs_bat + extras
            
            # Wicket detection
            wicket_type = parts[9] if len(parts) > 9 else ""
            player_out = parts[10] if len(parts) > 10 else ""
            is_wicket = 1 if (wicket_type and wicket_type.lower() not in ("", "none", "nan")) or player_out else 0

            balls.append({
                "Innings": innings,
                "Over": over_num,
                "Ball": ball_num,
                "Batting_Team": batting_team,
                "Batter": batter,
                "Non_Striker": non_striker,
                "Bowler": bowler,
                "Runs_Batter": runs_bat,
                "Extras": extras,
                "Total_Runs": total_runs,
                "Runs_From_Ball": total_runs,
                "Wicket": is_wicket,
                "IsBoundary": 1 if runs_bat in (4, 6) else 0,
                "IsDotBall": 1 if total_runs == 0 else 0,
            })
            
    df = pd.DataFrame(balls)
    if not df.empty:
        # Determine bowling team for each innings
        teams = meta.get("teams", [])
        if len(teams) >= 2:
            df["Bowling_Team"] = df["Innings"].apply(lambda inn: teams[1] if inn == 1 else teams[0])
        else:
            all_batting = df["Batting_Team"].unique().tolist()
            t1 = all_batting[0] if all_batting else "Team 1"
            t2 = all_batting[1] if len(all_batting) > 1 else "Team 2"
            df["Bowling_Team"] = df["Innings"].apply(lambda inn: t2 if inn == 1 else t1)
            
    return df, meta


@router.post(
    "/api/historical/upload",
    summary="Upload and analyze a historical match dataset",
    description=(
        "Processes a ball-by-ball CSV dataset, re-using Phase 3 ML models to generate "
        f"a match timeline. Max upload size: {_MAX_BYTES // (1024*1024)} MB."
    ),
)
async def upload_historical_match(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    # ── Size guard: read with a hard cap to avoid OOM on huge uploads ──
    content = await file.read(_MAX_BYTES + 1)
    if len(content) > _MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"File too large. Maximum allowed size is "
                f"{_MAX_BYTES // (1024 * 1024)} MB."
            ),
        )

    try:
        text_content = content.decode("utf-8", errors="ignore")
        lines = text_content.splitlines()
        
        meta: dict = {}
        is_cricsheet_raw = False
        
        # Detect Cricsheet raw structure
        if lines and (lines[0].startswith("version,") or any(l.startswith("info,") for l in lines[:15])):
            is_cricsheet_raw = True
            df, meta = _parse_raw_cricsheet(lines)
        else:
            df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")

    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="Uploaded CSV contains no valid ball records.")

    if not is_cricsheet_raw:
        # Strip whitespace from columns
        df.columns = [c.strip() for c in df.columns]

        # ── Robust Column Mapping for common datasets (Kaggle/Cricsheet) ──
        col_mapping = {
            "match_id": "Match_ID",
            "id": "Match_ID",
            "inning": "Innings",
            "innings": "Innings",
            "batting_team": "Batting_Team",
            "bat_team": "Batting_Team",
            "bowling_team": "Bowling_Team",
            "bowl_team": "Bowling_Team",
            "venue": "Venue",
            "striker": "Batter",
            "batsman": "Batter",
            "batter": "Batter",
            "bowler": "Bowler",
            "runs_off_bat": "Runs_Batter",
            "batsman_runs": "Runs_Batter",
            "extras": "Extras",
            "extra_runs": "Extras",
            "total_runs": "Total_Runs",
            "is_wicket": "Wicket",
            "wicket": "Wicket",
        }
        
        # Case-insensitive rename
        existing_cols = {c.lower(): c for c in df.columns}
        rename_dict = {}
        for alias, target in col_mapping.items():
            if alias.lower() in existing_cols:
                orig = existing_cols[alias.lower()]
                if orig != target:
                    rename_dict[orig] = target
        df.rename(columns=rename_dict, inplace=True)

        # Standardize Over and Ball from 'ball' column (e.g. 0.1, 0.2 Cricsheet notation)
        if "Ball" not in df.columns and "ball" in df.columns:
            df["Over"] = df["ball"].apply(lambda x: int(float(x))) + 1
            df["Ball"] = df["ball"].apply(lambda x: int(round((float(x) % 1) * 10)))
        elif "Over" not in df.columns:
            df["Over"] = (df.index // 6) + 1

        if "Ball" not in df.columns:
            df["Ball"] = (df.index % 6) + 1

        # If dataset contains multiple matches, filter to the first match
        if "Match_ID" in df.columns:
            first_match = df["Match_ID"].iloc[0]
            df = df[df["Match_ID"] == first_match].copy()

        # Score accumulation
        runs_bat = df["Runs_Batter"].fillna(0) if "Runs_Batter" in df.columns else pd.Series(0, index=df.index)
        extras = df["Extras"].fillna(0) if "Extras" in df.columns else pd.Series(0, index=df.index)
        if "Total_Runs" in df.columns:
            total_runs = df["Total_Runs"].fillna(0)
        else:
            total_runs = runs_bat + extras

        df["Runs_From_Ball"] = total_runs
        
        # Wicket accumulation
        if "Wicket" not in df.columns:
            wicket_col = next((c for c in ["dismissal_kind", "wicket_type", "player_dismissed"] if c in df.columns), None)
            if wicket_col:
                df["Wicket"] = (df[wicket_col].notna() & (df[wicket_col].astype(str).str.strip() != "") & (df[wicket_col].astype(str).str.lower() != "nan")).astype(int)
            else:
                df["Wicket"] = 0

        df["IsBoundary"] = df["Runs_Batter"].apply(lambda r: 1 if r in (4, 6) else 0) if "Runs_Batter" in df.columns else 0
        df["IsDotBall"] = df["Runs_From_Ball"].apply(lambda r: 1 if r == 0 else 0)

    try:
        # Standardize Innings column
        if "Innings" not in df.columns:
            df["Innings"] = 1
        else:
            df["Innings"] = pd.to_numeric(df["Innings"], errors="coerce").fillna(1).astype(int)

        # Separate Innings
        inn1_df = df[df["Innings"] == 1].copy()
        inn2_df = df[df["Innings"] == 2].copy()

        # Derive Teams
        team_a = str(inn1_df["Batting_Team"].iloc[0]) if not inn1_df.empty and "Batting_Team" in inn1_df.columns else (
            meta.get("teams", ["Team A", "Team B"])[0] if meta.get("teams") else "Team A"
        )
        team_b = str(inn2_df["Batting_Team"].iloc[0]) if not inn2_df.empty and "Batting_Team" in inn2_df.columns else (
            str(inn1_df["Bowling_Team"].iloc[0]) if not inn1_df.empty and "Bowling_Team" in inn1_df.columns else (
                meta.get("teams", ["Team A", "Team B"])[1] if len(meta.get("teams", [])) > 1 else "Team B"
            )
        )

        venue = meta.get("venue") or (str(df["Venue"].iloc[0]) if "Venue" in df.columns else "Historical Venue")
        season = meta.get("season") or (str(df["Season"].iloc[0]) if "Season" in df.columns else DEFAULT_SEASON)
        match_id = str(df["Match_ID"].iloc[0]) if "Match_ID" in df.columns else "Historical_Match"

        # ── Helper: build "X.Y ov" string from the last row of an innings df ───
        # Ball column stores 1-indexed ball-in-over (1–6).  Ball==6 means the
        # over is complete; anything less is mid-over (e.g. rain interruption).
        # A full T20 innings ends at over 20 ball 6  →  "20.0 ov" (completed).
        def _overs_str(inn_df: pd.DataFrame) -> str:
            if inn_df.empty:
                return "0.0"
            last_over = int(inn_df["Over"].iloc[-1])
            last_ball = int(inn_df["Ball"].iloc[-1])
            if last_ball >= 6:
                # Last delivery was the 6th ball → over is fully complete
                return f"{last_over}.0"
            else:
                return f"{last_over}.{last_ball}"

        # Calculate Innings 1 Final Summary
        inn1_total   = int(inn1_df["Runs_From_Ball"].sum()) if not inn1_df.empty else 0
        inn1_wickets = int(inn1_df["Wicket"].sum())         if not inn1_df.empty else 0
        inn1_last_over = int(inn1_df["Over"].iloc[-1])      if not inn1_df.empty else 20
        inn1_last_ball = int(inn1_df["Ball"].iloc[-1])      if not inn1_df.empty else 6
        inn1_overs_str = _overs_str(inn1_df)

        # Target for Innings 2 is Innings 1 Score + 1
        target = inn1_total + 1

        # Calculate Innings 2 Final Summary
        inn2_total   = int(inn2_df["Runs_From_Ball"].sum()) if not inn2_df.empty else 0
        inn2_wickets = int(inn2_df["Wicket"].sum())         if not inn2_df.empty else 0
        inn2_last_over = int(inn2_df["Over"].iloc[-1])      if not inn2_df.empty else 0
        inn2_last_ball = int(inn2_df["Ball"].iloc[-1])      if not inn2_df.empty else 0
        inn2_overs_str = _overs_str(inn2_df)

        # ── Compute True Match Winner and Margin ─────────────────────────────
        # Priority 1: use Cricsheet metadata (already has ground-truth winner/margin)
        if meta.get("winner"):
            winner = meta["winner"]
            if meta.get("winner_runs"):
                result_desc = f"{winner} won by {meta['winner_runs']} runs"
            elif meta.get("winner_wickets"):
                result_desc = f"{winner} won by {meta['winner_wickets']} wickets"
            else:
                result_desc = f"{winner} won the match"

        # Priority 2: derive from the actual ball data
        elif not inn2_df.empty:
            if inn2_total >= target:
                # Team B successfully chased — margin = wickets remaining
                # Wickets remaining = 10 minus wickets FALLEN (not out batters)
                winner = team_b
                wickets_remaining = max(0, 10 - inn2_wickets)
                result_desc = f"{team_b} won by {wickets_remaining} wicket{'s' if wickets_remaining != 1 else ''}"
            elif inn2_total < inn1_total:
                winner = team_a
                margin_runs = inn1_total - inn2_total
                result_desc = f"{team_a} won by {margin_runs} run{'s' if margin_runs != 1 else ''}"
            else:
                # Scores level — could be a tie or super over situation
                winner = "Match Tied"
                result_desc = "Match Tied (Super Over)"

        # Priority 3: only one innings in data (no result yet / first innings only)
        else:
            winner = "N/A"
            result_desc = f"{team_a} scored {inn1_total}/{inn1_wickets} ({inn1_overs_str} ov)"

        # ── Cumulative score/wickets per innings ─────────────────────────────
        # Use groupby transform so the result aligns back to the original df
        # index regardless of any sorting that happened in rolling features.
        df["Target"] = 0
        if not inn2_df.empty:
            df.loc[df["Innings"] == 2, "Target"] = target

        df["Current_Score"]   = df.groupby("Innings")["Runs_From_Ball"].transform("cumsum")
        df["Current_Wickets"] = df.groupby("Innings")["Wicket"].transform("cumsum")

        # ── Rolling feature calculation ───────────────────────────────────────
        for col in ["IsBoundary", "IsDotBall", "Wicket", "Runs_From_Ball"]:
            if col not in df.columns:
                df[col] = 0

        df = calculate_rolling_features(df)
        df = calculate_momentum_scores(df)
        df = calculate_partnership_features(df)

        # ── Snapshot at end of each over ──────────────────────────────────────
        # Drop-duplicates per (Innings, Over) preserving the last ball of each over.
        # Cap at 100 overs per innings (200 total) to avoid runaway processing on
        # Test-match data while keeping both innings fully represented.
        subset_cols = [c for c in ["Innings", "Over"] if c in df.columns]
        end_of_overs = df.drop_duplicates(subset=subset_cols, keep="last").copy()
        if len(end_of_overs) > 200:
            # Trim each innings independently so neither is silently lost
            inn1_snaps = end_of_overs[end_of_overs["Innings"] == 1].tail(100)
            inn2_snaps = end_of_overs[end_of_overs["Innings"] == 2].tail(100)
            end_of_overs = pd.concat([inn1_snaps, inn2_snaps]).sort_index()

        match_info = {
            "match_id": match_id,
            "team_a": team_a,
            "team_b": team_b,
            "batting_team": team_a,
            "bowling_team": team_b,
            "venue": venue,
            "season": season,
            "target": target,
            "team_a_score": f"{inn1_total}/{inn1_wickets} ({inn1_overs_str} ov)",
            "team_b_score": f"{inn2_total}/{inn2_wickets} ({inn2_overs_str} ov)" if not inn2_df.empty else "DNB",
            "winner": winner,
            "result_description": result_desc,
            "innings1_total": inn1_total,
            "innings1_wickets": inn1_wickets,
            "innings2_total": inn2_total,
            "innings2_wickets": inn2_wickets,
        }

        timeline: List[Dict[str, Any]] = []
        turning_points: List[Dict[str, Any]] = []

        total_points = len(end_of_overs)
        idx = 0

        for _, row in end_of_overs.iterrows():
            idx += 1
            curr_inn = int(row.get("Innings", 1))
            curr_batting = team_a if curr_inn == 1 else team_b
            curr_bowling = team_b if curr_inn == 1 else team_a
            
            state_dict = {
                "season": season,
                "venue": venue,
                "batting_team": curr_batting,
                "bowling_team": curr_bowling,
                "innings": curr_inn,
                "current_over": int(row.get("Over", 0)),
                "current_ball": int(row.get("Ball", 6)),
                "current_score": int(row.get("Current_Score", 0)),
                "current_wickets": int(row.get("Current_Wickets", 0)),
                "target": target if curr_inn == 2 else 0,
                "batter_name": str(row.get("Batter", "Unknown")),
                "bowler_name": str(row.get("Bowler", "Unknown")),
                "runs_last_6_balls": int(row.get("Runs_Last_6_Balls", 0)),
                "runs_last_12_balls": int(row.get("Runs_Last_12_Balls", 0)),
                "runs_last_18_balls": int(row.get("Runs_Last_18_Balls", 0)),
                "runs_last_30_balls": int(row.get("Runs_Last_30_Balls", 0)),
                "wickets_last_6_balls": int(row.get("Wickets_Last_6_Balls", 0)),
                "wickets_last_12_balls": int(row.get("Wickets_Last_12_Balls", 0)),
                "boundaries_last_6_balls": int(row.get("Boundaries_Last_6_Balls", 0)),
                "boundaries_last_12_balls": int(row.get("Boundaries_Last_12_Balls", 0)),
                "dot_balls_last_6_balls": int(row.get("Dot_Balls_Last_6_Balls", 0)),
                "dot_balls_last_12_balls": int(row.get("Dot_Balls_Last_12_Balls", 0)),
            }

            feature_row = model_store.build_feature_row(state_dict)
            mom_res = model_store.predict_momentum(feature_row)
            win_res = model_store.predict_win(feature_row, curr_batting, curr_bowling)

            # ── Win probability: normalise to consistent team_a / team_b keys ─
            # The model's predict_win output is keyed by curr_batting / curr_bowling.
            # We always want: team_a = innings-1 batting team, team_b = innings-2 batting team.
            raw_win_map = win_res.get("win_probability", {})

            def _pick_prob(primary_key: str, fallback_keys: list, raw: dict) -> float:
                """Look up a win probability, trying multiple possible key names."""
                if primary_key in raw:
                    return float(raw[primary_key])
                for k in fallback_keys:
                    if k in raw:
                        return float(raw[k])
                # Last resort: use the first numeric value present
                for v in raw.values():
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        pass
                return 50.0

            if curr_inn == 1:
                # In innings 1 the model is predicting for the batting team (team_a)
                p_a = _pick_prob(curr_batting, [team_a], raw_win_map)
                p_b = 100.0 - p_a
            else:
                # In innings 2 the model is predicting for the chasing team (team_b)
                p_b = _pick_prob(curr_batting, [team_b], raw_win_map)
                p_a = 100.0 - p_b
                # Pin final-ball result to the ground truth winner
                if idx == total_points:
                    if inn2_total >= target:
                        p_b = 100.0
                        p_a = 0.0
                    elif inn2_last_over >= 20 or inn2_wickets >= 10:
                        p_a = 100.0
                        p_b = 0.0

            consistent_win_prob = {
                team_a: round(float(p_a), 2),
                team_b: round(float(p_b), 2),
            }

            point = {
                "over": state_dict["current_over"],
                "innings": curr_inn,
                "score": state_dict["current_score"],
                "wickets": state_dict["current_wickets"],
                "momentum_class": mom_res["momentum_class"],
                "momentum_probabilities": mom_res["probabilities"],
                "win_probability": consistent_win_prob,
                "batter": state_dict["batter_name"],
                "bowler": state_dict["bowler_name"],
            }
            timeline.append(point)

            # Turning points detection
            if len(timeline) > 1 and mom_res["momentum_class"] != timeline[-2]["momentum_class"]:
                m_label = mom_res["momentum_class"]
                prev_label = timeline[-2]["momentum_class"]
                reason = build_turning_point_reason(
                    new_label=m_label,
                    prev_label=prev_label,
                    batting_team=curr_batting,
                    bowling_team=curr_bowling,
                    runs_last_12=int(row.get("Runs_Last_12_Balls", 0)),
                    wickets_last_12=int(row.get("Wickets_Last_12_Balls", 0)),
                    dot_balls_last_12=int(row.get("Dot_Balls_Last_12_Balls", 0)),
                    boundaries_last_12=int(row.get("Boundaries_Last_12_Balls", 0)),
                )
                turning_points.append({
                    "over": state_dict["current_over"],
                    "innings": curr_inn,
                    "description": (
                        f"Innings {curr_inn} — Momentum shifted to {m_label} at "
                        f"{state_dict['current_score']}/{state_dict['current_wickets']}"
                    ),
                    "win_prob": consistent_win_prob,
                    "reason": reason,
                })

        latest_state = timeline[-1] if timeline else {}

        result_payload = {
            "analysis_id": "hist_" + str(int(pd.Timestamp.now().timestamp())),
            "match_info": match_info,
            "timeline": timeline,
            "turning_points": turning_points,
            "latest_state": latest_state,
        }

        # Persist to activity DB
        try:
            log_historical_analysis(
                analysis_id=result_payload["analysis_id"],
                filename=file.filename or "unknown.csv",
                file_size_kb=len(content) / 1024,
                match_info=match_info,
                timeline_length=len(timeline),
                turning_points_count=len(turning_points),
                full_result=result_payload,
            )
        except Exception:
            pass

        return result_payload

    except Exception as e:
        logger.exception("Historical processing failed")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.get(
    "/api/historical/analysis/{analysis_id}",
    summary="Get persisted historical analysis result by ID",
    description="Fetches full timeline and turning points for a previously analyzed historical match dataset.",
)
async def get_historical_analysis(analysis_id: str):
    from backend.live.activity_db import get_historical_analysis_by_id
    result = get_historical_analysis_by_id(analysis_id)
    if result is None:
        raise HTTPException(404, detail=f"Historical analysis '{analysis_id}' not found.")
    return result

