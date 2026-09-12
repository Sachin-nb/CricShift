import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Pre-compiled patterns for ball event parsing
_DIGIT_RE = re.compile(r'\d+')
# Explicit extra type tokens (order matters — check widest pattern first)
_WIDE_RE    = re.compile(r'(?:\d+)?WD', re.IGNORECASE)
_NOBALL_RE  = re.compile(r'(?:\d+)?NB', re.IGNORECASE)
_LEGBYE_RE  = re.compile(r'(?:\d+)?LB', re.IGNORECASE)
_BYE_RE     = re.compile(r'(?:\d+)?B(?!OWLER)', re.IGNORECASE)
# A wicket token is a bare 'W' that is NOT part of WD/WB/NB/LB/SB/WICKET
_WICKET_RE  = re.compile(r'(?:\d+)?W(?!D|B|ICKET)', re.IGNORECASE)


def _parse_ball_event(ball_str: str) -> Dict[str, int]:
    """
    Parses a single ball result string from overHistory (e.g., '1', 'W', '6', '1LB', 'wd').
    Returns a dictionary: runs, is_wicket, is_boundary, is_dot, is_extra.
    """
    if not ball_str:
        return {"runs": 0, "is_wicket": 0, "is_boundary": 0, "is_dot": 0, "is_extra": 0}

    b = ball_str.strip()

    is_extra  = 1 if (_WIDE_RE.search(b) or _NOBALL_RE.search(b) or
                      _LEGBYE_RE.search(b) or _BYE_RE.search(b)) else 0
    is_wicket = 1 if _WICKET_RE.search(b) else 0

    nums = _DIGIT_RE.findall(b)
    runs = int(nums[0]) if nums else 0

    is_boundary = 1 if runs in (4, 6) else 0
    is_dot = 1 if (runs == 0 and not is_wicket and not is_extra) else 0

    return {
        "runs": runs,
        "is_wicket": is_wicket,
        "is_boundary": is_boundary,
        "is_dot": is_dot,
        "is_extra": is_extra,
    }


def _balls_to_cricket_over(completed_overs: int, ball_in_over: int) -> float:
    """
    Converts (completed_overs=1, ball_in_over=3) → 1.3 in cricket notation.
    After 6 balls the over is complete: returns (completed_overs + 1).0
    """
    if ball_in_over >= 6:
        return float(completed_overs + 1)
    return float(f"{completed_overs}.{ball_in_over}")


def normalize_live_data(scorecard: Dict, over_history: Dict, commentary: Dict) -> Dict[str, Any]:
    """
    Takes the raw RapidAPI responses (scorecard, overHistory, commentary)
    and flattens them into the exact schema expected by LiveFeatureAdapter.
    """
    state: Dict[str, Any] = {}

    # ── Scorecard ─────────────────────────────────────────────────────
    sc_data = scorecard.get("data", {})
    if "scorecard" in sc_data:
        sc = sc_data["scorecard"]
        innings_keys = [k for k in sc.keys() if str(k).isdigit()]
        if innings_keys:
            active_inning_key = max(innings_keys, key=int)
            active_inning = sc[active_inning_key]

            team_info = active_inning.get("team", {})
            state["current_score"]   = int(team_info.get("score",  0) or 0)
            state["current_wickets"] = int(team_info.get("wicket", 0) or 0)
            state["overs"]           = team_info.get("over", "0.0") if team_info.get("over") is not None else "0.0"
            state["batting_team"]    = team_info.get("name", "Unknown")
            state["innings"]         = int(team_info.get("inning", 1))

            # Bowling team — the other innings
            if len(innings_keys) > 1:
                other_key = min(innings_keys, key=int)
                state["bowling_team"] = sc[other_key].get("team", {}).get("name", "Bowling Team")
            else:
                state["bowling_team"] = "Bowling Team"

            # Striker
            batsmen = active_inning.get("batsman", {})
            if isinstance(batsmen, dict) and batsmen:
                first_bat = next(iter(batsmen.values()))
                state["current_striker"] = (
                    first_bat.get("name", "Unknown")
                    .replace("(C)", "").replace("(W)", "").strip()
                )
            elif isinstance(batsmen, list) and batsmen:
                state["current_striker"] = (
                    batsmen[0].get("name", "Unknown")
                    .replace("(C)", "").replace("(W)", "").strip()
                )

            # Bowler — API typo "bolwer" is intentional in some versions
            bowlers = active_inning.get("bolwer") or active_inning.get("bowler", {})
            if isinstance(bowlers, dict) and bowlers:
                first_bowl = next(iter(bowlers.values()))
                state["current_bowler"] = first_bowl.get("name", "Unknown").strip()
            elif isinstance(bowlers, list) and bowlers:
                state["current_bowler"] = bowlers[0].get("name", "Unknown").strip()

            # Partnership
            partnerships = active_inning.get("partnership", {})
            if isinstance(partnerships, dict) and partnerships:
                last_p = list(partnerships.values())[-1]
                state["partnership_runs"]  = last_p.get("run",  0)
                state["partnership_balls"] = last_p.get("ball", 1)
            elif isinstance(partnerships, list) and partnerships:
                last_p = partnerships[-1]
                state["partnership_runs"]  = last_p.get("run",  0)
                state["partnership_balls"] = last_p.get("ball", 1)

    # ── Over history ──────────────────────────────────────────────────
    oh_data = over_history.get("data", {})
    target   = 0
    cr_rate  = 0.0
    rr_rate  = 0.0
    runs_need = 0
    ball_rem  = 0

    # Collect all ball events with (completed_over_0indexed, ball_in_over) for
    # correct cricket-notation over values and chronological sorting.
    # Expected structure (from API or mock):
    #   oh_data = {
    #     "<innings_key>": {
    #       "<over_index>": {
    #         "team":  {"over": <1-based over num>, "cr_rate": ..., ...},
    #         "overs": {"0": "<ball_str>", "1": "<ball_str>", ...}
    #       },
    #       ...
    #     },
    #     ...
    #   }
    all_balls_raw: List[Dict] = []   # {completed_over: int, ball_in_over: int, raw: str}

    for inn_key, inn_data in oh_data.items():
        if inn_key == "_meta" or not isinstance(inn_data, dict):
            continue

        # Sort over-index keys numerically so we process overs chronologically
        try:
            sorted_over_keys = sorted(inn_data.keys(), key=lambda x: int(x))
        except (ValueError, TypeError):
            sorted_over_keys = list(inn_data.keys())

        for over_idx_key in sorted_over_keys:
            over_obj = inn_data[over_idx_key]
            if not isinstance(over_obj, dict):
                continue

            t_obj = over_obj.get("team", {})

            # Harvest chase metadata from the most recent over seen
            for field, target_var in [
                ("cr_rate",  "cr_rate"),
                ("rr_rate",  "rr_rate"),
                ("run_need", "runs_need"),
                ("ball_rem", "ball_rem"),
            ]:
                if field in t_obj:
                    try:
                        val = float(t_obj[field])
                        if field == "run_need":
                            runs_need = int(val)
                        elif field == "ball_rem":
                            ball_rem = int(val)
                        elif field == "cr_rate":
                            cr_rate = val
                        elif field == "rr_rate":
                            rr_rate = val
                    except (ValueError, TypeError):
                        pass

            # The 1-based over number from the API (e.g. 1, 2, … 15)
            try:
                api_over_num = int(t_obj.get("over", over_idx_key))
            except (ValueError, TypeError):
                try:
                    api_over_num = int(over_idx_key) + 1
                except (ValueError, TypeError):
                    api_over_num = 1

            # 0-based completed overs before this over starts
            completed_overs_before = api_over_num - 1

            ov_events = over_obj.get("overs", {})
            if isinstance(ov_events, dict):
                try:
                    sorted_balls = sorted(ov_events.items(), key=lambda x: int(x[0]))
                except (ValueError, TypeError):
                    sorted_balls = list(ov_events.items())

                for ball_idx, (_, ball_val) in enumerate(sorted_balls):
                    all_balls_raw.append({
                        "completed_over": completed_overs_before,
                        "ball_in_over":   ball_idx + 1,   # 1-based within this over
                        "raw": str(ball_val),
                    })

    # Sort all collected balls globally: primary = completed_over, secondary = ball_in_over
    all_balls_raw.sort(key=lambda x: (x["completed_over"], x["ball_in_over"]))

    # ── Fallback to commentary if over history was empty ─────────────
    if not all_balls_raw:
        comm_data = commentary.get("data", {})
        comm_list = []
        if "commentary" in comm_data:
            comm_list = comm_data["commentary"]
        elif isinstance(comm_data, list):
            comm_list = comm_data

        for c in reversed(comm_list):   # API returns newest first
            if isinstance(c, dict) and "ball" in c:
                try:
                    ball_str = str(c["ball"])
                    if "." in ball_str:
                        ov_part, b_part = ball_str.split(".", 1)
                        b_val = (
                            c.get("comm", "").split(",")[0].split(" ")[0].strip()
                        )
                        all_balls_raw.append({
                            "completed_over": int(ov_part),
                            "ball_in_over":   int(b_part),
                            "raw": b_val if b_val else "0",
                        })
                except Exception:
                    pass

        all_balls_raw.sort(key=lambda x: (x["completed_over"], x["ball_in_over"]))

    # ── Build recent_overs string (last 30 legal deliveries) ─────────
    recent_30 = [b["raw"] for b in all_balls_raw[-30:]]
    state["recent_overs"] = " ".join(recent_30)

    # ── Build all_balls_parsed with cricket-notation over values ─────
    state["all_balls_parsed"] = []
    cumulative_runs     = 0
    cumulative_wickets  = 0

    for b in all_balls_raw:
        parsed = _parse_ball_event(b["raw"])
        cumulative_runs    += parsed["runs"]
        cumulative_wickets += parsed["is_wicket"]

        cricket_over = _balls_to_cricket_over(b["completed_over"], b["ball_in_over"])

        state["all_balls_parsed"].append({
            "over":                cricket_over,
            "ball_idx":            b["ball_in_over"],
            "raw":                 b["raw"],
            "runs":                parsed["runs"],
            "is_wicket":           parsed["is_wicket"],
            "is_boundary":         parsed["is_boundary"],
            "is_dot":              parsed["is_dot"],
            "cumulative_runs":     cumulative_runs,
            "cumulative_wickets":  cumulative_wickets,
        })

    # ── Target derivation for Innings 2 ──────────────────────────────
    current_score = state.get("current_score", 0)
    if runs_need > 0 and current_score > 0:
        # runs_need is runs still required, so target = current + still_needed
        state["target"] = current_score + runs_need
    elif runs_need <= 0 and ball_rem > 0 and current_score > 0:
        # already passed target — try to infer from completed innings in scorecard
        sc_data2 = scorecard.get("data", {})
        sc2 = sc_data2.get("scorecard", {})
        inn_keys = [k for k in sc2.keys() if str(k).isdigit()]
        if len(inn_keys) >= 2:
            first_inn_key = min(inn_keys, key=int)
            first_inn_score = sc2[first_inn_key].get("team", {}).get("score", 0)
            state["target"] = int(first_inn_score) + 1
        else:
            state["target"] = 0
    else:
        state["target"] = 0

    # Innings length (overs) derived from the live feed, threaded via _meta.
    state["max_overs"] = int((oh_data.get("_meta") or {}).get("max_overs", 0) or 0)

    return state
