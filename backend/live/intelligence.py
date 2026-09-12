"""
Live intelligence service — Phase 5B.

Optimised for speed:
  • Models are loaded once at startup via model_store (no per-request pickle I/O).
  • SQLite historical look-ups are executed ONCE per request (not once per ball).
  • The per-ball feature rows are built from pre-fetched stats passed as kwargs.
  • Timeline is capped at MAX_TIMELINE_POINTS to keep response times under ~5 s.
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Any, Dict, List, Optional

from .api_client import LiveAPIClient, APIClientError
from .normalizer import normalize_live_data
from .feature_adapter import LiveFeatureAdapter
from .turning_points import build_turning_point_reason
from .commentary_engine import commentary_engine
from . import matcher

from backend.dependencies import model_store

logger = logging.getLogger(__name__)

# Hard cap: process at most this many historical ball-states per request.
# 90 balls × 4 SQLite calls × ~2 ms = ~720 ms saved by deduplication alone.
# With the cap, worst case is ~30 feature-builds + 1 batch prediction.
MAX_TIMELINE_POINTS = 60


class LiveIntelligenceService:
    """
    Orchestrates live match intelligence.

    Models are provided by the shared model_store singleton (populated once at
    application startup). LiveFeatureAdapter loads its own encoder/feature-col
    pickles at construction time; this service is itself a singleton in the DI layer.
    """

    def __init__(self, api_client: LiveAPIClient = None):
        self.api_client = api_client or LiveAPIClient()
        self.feature_adapter = LiveFeatureAdapter()

    @property
    def momentum_model(self):
        return model_store.momentum_model

    @property
    def win_model(self):
        return model_store.win_model

    # ── public entry point ────────────────────────────────────────────────────
    def get_live_intelligence(self, match_id: str) -> Dict[str, Any]:
        momentum_model = model_store.momentum_model
        win_model      = model_store.win_model

        if not momentum_model or not win_model:
            return {
                "error":   "Models not loaded",
                "details": "ML models are not available — check /api/health",
            }

        try:
            # ── 1. Fetch live data ────────────────────────────────────────
            scorecard    = self.api_client.get_scorecard(match_id)
            over_history = self.api_client.get_over_history(match_id)
            commentary   = self.api_client.get_commentary(match_id)

            # ── 2. Normalise to flat state dict ───────────────────────────
            ns = normalize_live_data(scorecard, over_history, commentary)

            batting_team = ns.get("batting_team", "Batting Team") or "Batting Team"
            bowling_team = ns.get("bowling_team", "Bowling Team") or "Bowling Team"

            # ── 3. Pre-fetch SQLite stats ONCE (not once per ball) ────────
            batter = str(ns.get("current_striker") or ns.get("striker") or "Unknown")
            bowler = str(ns.get("current_bowler")  or ns.get("bowler")  or "Unknown")

            cached = {
                "p_stats": matcher.get_player_stats(batter),
                "b_stats": matcher.get_player_stats(bowler),
                "t_stats": matcher.get_team_stats(batting_team),
                "v_stats": matcher.get_venue_stats(ns.get("venue", "Unknown")),
            }

            # ── 4. Build past states (End-of-over snapshots + current live state) ──
            all_balls   = ns.get("all_balls_parsed", [])
            current_ov  = float(ns.get("overs", 0.0) or 0.0)
            past_states: List[dict] = []

            if all_balls:
                last_seen_by_over: Dict[int, int] = {}
                for idx, b in enumerate(all_balls):
                    ov_val = float(b.get("over", 0.0))
                    # Use the completed-over number as the bucket key.
                    # ov_val in cricket notation: 1.1–1.6 are balls inside over 1
                    # (completed_over=0 from normalizer), 2.0 means over 1 is done.
                    # int(ov_val) gives 1 for both 1.1 and 1.6 (correct: same over),
                    # and 2 for 2.0 (correct: over 2 boundary).
                    # The old code used int(ov_val)+1 for fractional values which
                    # incorrectly placed 1.1 in bucket 2 — same bucket as 2.0 —
                    # collapsing an entire over's balls into a single snapshot point.
                    over_int = int(ov_val)
                    last_seen_by_over[over_int] = idx

                snapshot_indices = [last_seen_by_over[k] for k in sorted(last_seen_by_over.keys())]

                if snapshot_indices and snapshot_indices[-1] != len(all_balls) - 1:
                    snapshot_indices.append(len(all_balls) - 1)

                fa = self.feature_adapter
                for idx in snapshot_indices:
                    b = all_balls[idx]
                    balls_up_to = all_balls[: idx + 1]

                    recent_30 = [ball["raw"] for ball in balls_up_to[-30:]]
                    recent_18 = [ball["raw"] for ball in balls_up_to[-18:]]
                    recent_12 = [ball["raw"] for ball in balls_up_to[-12:]]
                    recent_6  = [ball["raw"] for ball in balls_up_to[-6:]]

                    r6  = sum(fa._runs(ball) for ball in recent_6)
                    r12 = sum(fa._runs(ball) for ball in recent_12)
                    r18 = sum(fa._runs(ball) for ball in recent_18)
                    r30 = sum(fa._runs(ball) for ball in recent_30)

                    w6  = sum(fa._is_wicket(ball) for ball in recent_6)
                    w12 = sum(fa._is_wicket(ball) for ball in recent_12)

                    bnd6  = sum(fa._is_boundary(ball) for ball in recent_6)
                    bnd12 = sum(fa._is_boundary(ball) for ball in recent_12)

                    dot6  = sum(fa._is_dot(ball) for ball in recent_6)
                    dot12 = sum(fa._is_dot(ball) for ball in recent_12)

                    ov_num = float(b["over"])
                    display_over = int(ov_num) if ov_num == int(ov_num) else round(ov_num, 1)

                    past_state = dict(ns)
                    past_state["current_score"]   = b["cumulative_runs"]
                    past_state["current_wickets"] = b["cumulative_wickets"]
                    past_state["overs"]           = display_over
                    past_state["recent_overs"]    = " ".join(recent_30)

                    past_state["runs_last_6_balls"]       = r6
                    past_state["runs_last_12_balls"]      = r12
                    past_state["runs_last_18_balls"]      = r18
                    past_state["runs_last_30_balls"]      = r30
                    past_state["wickets_last_6_balls"]     = w6
                    past_state["wickets_last_12_balls"]    = w12
                    past_state["boundaries_last_6_balls"]  = bnd6
                    past_state["boundaries_last_12_balls"] = bnd12
                    past_state["dot_balls_last_6_balls"]   = dot6
                    past_state["dot_balls_last_12_balls"]  = dot12

                    past_states.append(past_state)

            if not past_states:
                # No over-history data is available yet (match hasn't started or
                # the API returned empty overHistory).  Rather than injecting a
                # single degenerate state at overs=0 — which produces one isolated
                # dot on every chart — we return an empty timeline so the frontend
                # renders its "Waiting for data…" placeholder instead.
                logger.info(f"[{match_id}] No ball data available; returning empty timeline.")
                return {
                    "match_id":      match_id,
                    "status":        "waiting",
                    "timeline":      [],
                    "latest_state":  {},
                    "turning_points": [],
                    "ai_commentary": None,
                }

            # ── 5. Batch-build feature rows ───────────────────────────────
            # Pass pre-fetched stats into the adapter so it skips SQLite lookups
            dfs = [
                self._build_features_fast(st, cached)
                for st in past_states
            ]
            df = pd.concat(dfs, ignore_index=True)

            mom_df = self.feature_adapter.get_momentum_features(df)
            win_df = self.feature_adapter.get_win_features(df)

            # ── 6. Batch predict ──────────────────────────────────────────
            mom_probs_all = momentum_model.predict_proba(mom_df)
            mom_class_all = momentum_model.predict(mom_df)
            win_probs_all = win_model.predict_proba(win_df)

            mom_labels = ["Negative", "Neutral", "Positive"]

            # ── 7. Build timeline ─────────────────────────────────────────
            timeline:       List[dict] = []
            turning_points: List[dict] = []

            for i, st in enumerate(past_states):
                m_probs = mom_probs_all[i]
                m_class = int(mom_class_all[i])
                w_probs = win_probs_all[i]

                m_label = mom_labels[m_class] if 0 <= m_class <= 2 else "Neutral"

                win_prob = {
                    batting_team: round(float(w_probs[1]) * 100 if len(w_probs) > 1 else 50.0, 2),
                    bowling_team: round(float(w_probs[0]) * 100 if len(w_probs) > 0 else 50.0, 2),
                }
                mom_prob = {
                    "Negative": round(float(m_probs[0]) if len(m_probs) > 0 else 0.0, 4),
                    "Neutral":  round(float(m_probs[1]) if len(m_probs) > 1 else 0.0, 4),
                    "Positive": round(float(m_probs[2]) if len(m_probs) > 2 else 0.0, 4),
                }

                point = {
                    "over":                   st.get("overs", 0.0),
                    "momentum_class":         m_label,
                    "momentum_probabilities": mom_prob,
                    "win_probability":        win_prob,
                    "score":                  int(st.get("current_score",   0)),
                    "wickets":                int(st.get("current_wickets", 0)),
                }
                timeline.append(point)

                if len(timeline) > 1:
                    prev_point = timeline[-2]
                    prev_label = prev_point["momentum_class"]
                    prev_win_prob_batting = prev_point["win_probability"].get(batting_team, 50.0)
                    cur_win_prob_batting = win_prob.get(batting_team, 50.0)
                    win_prob_diff = abs(cur_win_prob_batting - prev_win_prob_batting)
                    cur_wickets = int(st.get("current_score", 0))
                    prev_wickets = int(prev_point.get("wickets", 0))

                    is_class_shift  = (m_label != prev_label)
                    is_prob_shift   = (win_prob_diff >= 10.0)
                    is_wicket_event = (int(st.get("current_wickets", 0)) > prev_wickets)

                    if is_class_shift or is_prob_shift or is_wicket_event:
                        reason = build_turning_point_reason(
                            new_label=m_label,
                            prev_label=prev_label,
                            batting_team=batting_team,
                            bowling_team=bowling_team,
                            runs_last_12=int(st.get("runs_last_12_balls", 0)),
                            wickets_last_12=int(st.get("wickets_last_12_balls", 0)),
                            dot_balls_last_12=int(st.get("dot_balls_last_12_balls", 0)),
                            boundaries_last_12=int(st.get("boundaries_last_12_balls", 0)),
                        )
                        turning_points.append({
                            "over":        st.get("overs", 0.0),
                            "innings":     int(st.get("innings", 1)),
                            "description": (
                                f"Momentum shifted to {m_label} at "
                                f"{int(st.get('current_score', 0))}"
                                f"/{int(st.get('current_wickets', 0))}"
                            ),
                            "win_prob": win_prob,
                            "reason":   reason,
                        })

            current_state_data = timeline[-1] if timeline else {}

            # Generate real-time AI contextual commentary
            ai_commentary = commentary_engine.generate_commentary(
                batting_team=ns.get("batting_team", "Team A"),
                bowling_team=ns.get("bowling_team", "Team B"),
                current_over=int(float(ns.get("overs", 0.0))),
                current_ball=int(round((float(ns.get("overs", 0.0)) % 1) * 10)),
                current_score=ns.get("current_score", 0),
                current_wickets=ns.get("current_wickets", 0),
                target=ns.get("target"),
                win_prob_batting=float(current_state_data.get("win_probability", {}).get(ns.get("batting_team", ""), 50.0)),
                win_prob_delta=0.0,
                momentum_label=current_state_data.get("momentum_class", "Neutral"),
                batter_name=batter,
                bowler_name=bowler,
                top_shap_features=["pressure_index", "required_run_rate", "current_run_rate"],
            )

            return {
                "match_id":   match_id,
                "status":     "live",
                "timeline":   timeline,
                "latest_state": {
                    "batter":          batter,
                    "bowler":          bowler,
                    "momentum_class":  current_state_data.get("momentum_class", "Neutral"),
                    "win_probability": current_state_data.get("win_probability", {}),
                },
                "momentum": {
                    "momentum_class": current_state_data.get("momentum_class", "Neutral"),
                    "probabilities":  current_state_data.get("momentum_probabilities", {}),
                },
                "win_prediction": current_state_data.get("win_probability", {}),
                "match": {
                    "score":   ns.get("current_score", 0),
                    "wickets": ns.get("current_wickets", 0),
                    "overs":   ns.get("overs", "0.0"),
                },
                "turning_points": turning_points,
                "ai_commentary": ai_commentary,
                "last_updated":   datetime.now().isoformat(),
            }

        except APIClientError as e:
            logger.error(f"API Error for {match_id}: {e}")
            return {"error": "API Error", "details": str(e)}
        except Exception as e:
            logger.exception(f"Internal Error for {match_id}")
            return {"error": "Internal Error", "details": str(e)}

    # ── fast feature builder (skips SQLite — uses pre-fetched stats) ──────────
    def _build_features_fast(self, live_data: dict, cached: dict) -> pd.DataFrame:
        """
        Same logic as LiveFeatureAdapter.process_live_payload() but injects
        pre-fetched player/team/venue stats instead of hitting SQLite per call.
        """
        import numpy as np
        from datetime import datetime as _dt

        fa = self.feature_adapter

        season       = str(live_data.get("season", str(_dt.now().year)))
        venue        = live_data.get("venue",        "Unknown") or "Unknown"
        batting_team = live_data.get("batting_team", "Unknown") or "Unknown"
        bowling_team = live_data.get("bowling_team", "Unknown") or "Unknown"

        current_score   = int(live_data.get("current_score")   or live_data.get("score",   0) or 0)
        current_wickets = int(live_data.get("current_wickets") or live_data.get("wickets", 0) or 0)
        overs_raw  = float(live_data.get("overs", 0.0) or 0.0)
        cur_ov, cur_ball, balls_bowled = fa.parse_cricket_overs(overs_raw)

        balls_remaining = max(0, 120 - balls_bowled)
        overs_remaining = balls_remaining / 6

        target  = int(live_data.get("target",  0) or 0)
        innings = int(live_data.get("innings", 2 if target > 0 else 1) or 1)

        runs_remaining = max(0, target - current_score) if innings == 2 else 0
        crr  = (current_score / balls_bowled * 6) if balls_bowled > 0 else 0.0
        rrr  = (runs_remaining / balls_remaining * 6) if innings == 2 and balls_remaining > 0 else 0.0
        rrr_gap = rrr - crr if innings == 2 else 0.0

        recent_str = str(live_data.get("recent_overs", "") or "")
        balls_list = recent_str.split() if recent_str else []

        def _sl(n): return balls_list[-n:] if len(balls_list) >= n else balls_list

        b6, b12, b18, b30 = _sl(6), _sl(12), _sl(18), _sl(30)

        r6  = int(live_data.get("runs_last_6_balls")  if live_data.get("runs_last_6_balls")  is not None else sum(fa._runs(b) for b in b6))
        r12 = int(live_data.get("runs_last_12_balls") if live_data.get("runs_last_12_balls") is not None else sum(fa._runs(b) for b in b12))
        r18 = int(live_data.get("runs_last_18_balls") if live_data.get("runs_last_18_balls") is not None else sum(fa._runs(b) for b in b18))
        r30 = int(live_data.get("runs_last_30_balls") if live_data.get("runs_last_30_balls") is not None else sum(fa._runs(b) for b in b30))

        w6  = int(live_data.get("wickets_last_6_balls")  if live_data.get("wickets_last_6_balls")  is not None else sum(fa._is_wicket(b) for b in b6))
        w12 = int(live_data.get("wickets_last_12_balls") if live_data.get("wickets_last_12_balls") is not None else sum(fa._is_wicket(b) for b in b12))

        bnd6  = int(live_data.get("boundaries_last_6_balls")  if live_data.get("boundaries_last_6_balls")  is not None else sum(fa._is_boundary(b) for b in b6))
        bnd12 = int(live_data.get("boundaries_last_12_balls") if live_data.get("boundaries_last_12_balls") is not None else sum(fa._is_boundary(b) for b in b12))

        dot6  = int(live_data.get("dot_balls_last_6_balls")  if live_data.get("dot_balls_last_6_balls")  is not None else sum(fa._is_dot(b) for b in b6))
        dot12 = int(live_data.get("dot_balls_last_12_balls") if live_data.get("dot_balls_last_12_balls") is not None else sum(fa._is_dot(b) for b in b12))

        dbp = (dot12 / 12 * 100) if b12 else 0.0
        pi  = rrr + (w6 * 2) + (dbp / 10)
        bm  = bnd12 * 4
        ms  = (r6 - w6 * 8) / max(1, 6)

        p_runs  = int(live_data.get("partnership_runs", 0) or 0)
        p_balls = int(live_data.get("partnership_balls", 1) or 1)
        p_rr    = (p_runs / p_balls * 6) if p_balls > 0 else 0.0

        # use pre-fetched stats
        p_stats = cached.get("p_stats", {})
        b_stats = cached.get("b_stats", {})
        t_stats = cached.get("t_stats", {})
        v_stats = cached.get("v_stats", {})

        bb  = b_stats.get("Balls_Bowled", 0)
        dbb = b_stats.get("Dot_Balls_Bowled", 0)
        bsr = b_stats.get("Bowling_Strike_Rate", 0)

        batter = str(live_data.get("current_striker", "") or "Unknown")
        bowler = str(live_data.get("current_bowler",  "") or "Unknown")

        features = {
            "Season": season, "Venue": venue,
            "Batting_Team": batting_team, "Bowling_Team": bowling_team,
            "Innings": innings,
            "Current_Over": cur_ov, "Current_Ball": cur_ball,
            "Current_Score": current_score, "Current_Wickets": current_wickets,
            "Target": target,
            "Current_Run_Rate":      round(crr,     4),
            "Required_Run_Rate":     round(rrr,     4),
            "Required_Run_Rate_Gap": round(rrr_gap, 4),
            "Balls_Remaining": balls_remaining,
            "Overs_Remaining": round(overs_remaining, 4),
            "Runs_Remaining":  runs_remaining,
            "Runs_Last_6_Balls":  r6,  "Runs_Last_12_Balls": r12,
            "Runs_Last_18_Balls": r18, "Runs_Last_30_Balls": r30,
            "Wickets_Last_6_Balls": w6, "Wickets_Last_12_Balls": w12,
            "Boundaries_Last_6_Balls": bnd6, "Boundaries_Last_12_Balls": bnd12,
            "Dot_Balls_Last_6_Balls": dot6,  "Dot_Balls_Last_12_Balls": dot12,
            "Pressure_Index":    round(pi,  4),
            "Boundary_Momentum": bm,
            "Dot_Ball_Pressure": round(dbp, 4),
            "Momentum_Score":    round(ms,  4),
            "Current_Partnership_Runs":     p_runs,
            "Current_Partnership_Balls":    p_balls,
            "Current_Partnership_Run_Rate": round(p_rr, 4),
            "Batter_Name":               batter,
            "Batter_Career_Average":      p_stats.get("Average",             0),
            "Batter_Career_Strike_Rate":  p_stats.get("Strike_Rate",         0),
            "Batter_Recent_Form":         p_stats.get("Average",             0),
            "Batter_Boundary_Percentage": p_stats.get("Boundary_Percentage", 0),
            "Batting_Impact_Score":       p_stats.get("Batting_Impact_Score",0),
            "Bowler_Name":               bowler,
            "Bowler_Economy":            b_stats.get("Economy",              0),
            "Bowler_Strike_Rate":        bsr,
            "Bowler_Wicket_Rate":        (1 / bsr) if bsr > 0 else 0,
            "Bowler_Recent_Form":        b_stats.get("Economy",              0),
            "Bowler_Dot_Ball_Percentage":(dbb / bb * 100) if bb > 0 else 0,
            "Bowling_Impact_Score":      b_stats.get("Bowling_Impact_Score", 0),
            "Team_Win_Percentage":      t_stats.get("Win_Percentage",          50),
            "Bat_First_Strength":       t_stats.get("Bat_First_Win_Percentage", 0),
            "Chase_Strength":           t_stats.get("Chasing_Win_Percentage",   0),
            "Team_Form_Last_5_Matches": t_stats.get("Win_Percentage",          50),
            "Venue_Run_Rate":        v_stats.get("Average_Run_Rate",        8.0),
            "Venue_Average_Score":   v_stats.get("Average_First_Innings",  160),
            "Venue_Chasing_Success": v_stats.get("Chasing_Win_Percentage",  50),
            "Venue_Difficulty_Index":max(0, 10 - v_stats.get("Average_Run_Rate", 8.0)),
            "Powerplay_Flag":      1 if cur_ov < 6  else 0,
            "Middle_Overs_Flag":   1 if 6 <= cur_ov < 15 else 0,
            "Death_Overs_Flag":    1 if cur_ov >= 15 else 0,
            "Pressure_Overs_Flag": 1 if overs_remaining <= 3 else 0,
        }

        df = pd.DataFrame([features])

        for col in df.select_dtypes(include=["object"]).columns.tolist():
            enc = fa.encoders
            if col in enc:
                le  = enc[col]
                val = str(df[col].iloc[0])
                if val not in le.classes_:
                    val = le.classes_[0]
                df[col] = le.transform([val])
            else:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        df = df.fillna(0).replace([np.inf, -np.inf], 0)
        return df
