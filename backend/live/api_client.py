import os
import os
import requests
import logging
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment from BOTH the project-root .env and backend/.env using
# absolute paths, so RAPIDAPI_KEY/RAPIDAPI_HOST are found regardless of the
# process working directory (uvicorn may be launched from anywhere).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv(_PROJECT_ROOT / "backend" / ".env")

logger = logging.getLogger(__name__)

class APIClientError(Exception):
    pass


# ═════════════════════════════════════════════════════════════════════════════
# Mock data catalog — multiple varied, fully-populated live matches.
# Used as a graceful fallback whenever the real RapidAPI call fails / is
# rate-limited / returns no data, so the UI is never blank.
# ═════════════════════════════════════════════════════════════════════════════

def _build_over_scripts(balls_per_over_seq, target: int):
    """
    Turn a list of per-over ball-result lists into the overHistory 'script'
    shape: (over_num, balls, cr_rate, run_need, ball_rem). Computes running
    run_need / ball_rem / cr_rate from the actual ball outcomes so the numbers
    stay internally consistent for any match.
    """
    scripts = []
    cumulative = 0
    balls_done = 0
    for i, balls in enumerate(balls_per_over_seq):
        ov_num = i + 1
        for b in balls:
            balls_done += 1
            if b.isdigit():
                cumulative += int(b)
        ball_rem = max(0, 120 - balls_done)
        run_need = max(-999, target - cumulative) if target else 0
        cr_rate = round(cumulative / balls_done * 6, 2) if balls_done else 0.0
        scripts.append((ov_num, balls, cr_rate, run_need, ball_rem))
    return scripts


# Each match: two innings (innings[0] = completed/first, innings[1] = live chase).
_MOCK_MATCHES: Dict[str, Dict[str, Any]] = {
    "99999": {
        "series": "Premier T20 League 2024",
        "desc":   "Final",
        "venue":  "Wankhede Stadium, Mumbai",
        "target": 173,
        "innings": [
            {
                "team": "Chennai Super Kings", "score": 172, "wicket": 5, "over": 20.0,
                "batsman": {
                    "1": {"name": "Ruturaj Gaikwad", "run": 68, "ball": 47, "sr": 144.68},
                    "2": {"name": "Devon Conway",    "run": 52, "ball": 38, "sr": 136.84},
                },
                "bolwer": {
                    "1": {"name": "Jasprit Bumrah", "over": "4.0", "run": 28, "wicket": 2, "eco": 7.0},
                },
            },
            {
                "team": "Mumbai Indians", "score": 145, "wicket": 4, "over": 15.4,
                "batsman": {
                    "1": {"name": "Suryakumar Yadav", "run": 45, "ball": 30, "sr": 150.0},
                    "2": {"name": "Tilak Varma",       "run": 28, "ball": 22, "sr": 127.27},
                },
                "bolwer": {
                    "1": {"name": "Ravindra Jadeja", "over": "3.4", "run": 24, "wicket": 1, "eco": 6.55},
                },
            },
        ],
        "balls": [
            ["1","0","4","1","2","0"], ["6","1","0","4","W","0"], ["1","1","2","0","4","1"],
            ["0","6","1","1","0","4"], ["4","1","W","0","2","1"], ["1","0","0","4","6","1"],
            ["2","1","4","0","1","W"], ["0","6","1","4","1","0"], ["4","1","1","2","0","6"],
            ["1","W","4","0","6","1"], ["6","4","1","0","1","2"], ["1","0","W","4","1","6"],
            ["4","6","1","1","0","4"], ["1","0","4","2","1","W"], ["6","4","1","0"],
        ],
        "commentary": [
            {"ball": "15.4", "comm": "SIX! Suryakumar goes downtown!"},
            {"ball": "15.3", "comm": "FOUR! Driven through covers."},
            {"ball": "15.2", "comm": "1 run, worked to midwicket."},
            {"ball": "15.1", "comm": "Dot ball, defended."},
        ],
    },
    "88888": {
        "series": "Premier T20 League 2024",
        "desc":   "Qualifier 2",
        "venue":  "Eden Gardens, Kolkata",
        "target": 191,
        "innings": [
            {
                "team": "Royal Challengers Bengaluru", "score": 190, "wicket": 6, "over": 20.0,
                "batsman": {
                    "1": {"name": "Virat Kohli",  "run": 82, "ball": 53, "sr": 154.7},
                    "2": {"name": "Faf du Plessis","run": 41, "ball": 29, "sr": 141.3},
                },
                "bolwer": {"1": {"name": "Varun Chakravarthy", "over": "4.0", "run": 31, "wicket": 2, "eco": 7.75}},
            },
            {
                "team": "Kolkata Knight Riders", "score": 88, "wicket": 3, "over": 10.2,
                "batsman": {
                    "1": {"name": "Shreyas Iyer",   "run": 39, "ball": 27, "sr": 144.4},
                    "2": {"name": "Andre Russell",  "run": 22, "ball": 11, "sr": 200.0},
                },
                "bolwer": {"1": {"name": "Mohammed Siraj", "over": "3.0", "run": 19, "wicket": 1, "eco": 6.33}},
            },
        ],
        "balls": [
            ["0","1","4","1","0","6"], ["1","4","0","1","W","2"], ["6","0","1","1","4","0"],
            ["1","1","0","4","2","1"], ["W","0","4","1","1","6"], ["1","2","0","0","4","1"],
            ["4","6","1","1","0","W"], ["0","1","4","2","1","1"], ["6","1","0","4","1","2"],
            ["1","4","0","2"],
        ],
        "commentary": [
            {"ball": "10.2", "comm": "FOUR! Russell muscles it over mid-on."},
            {"ball": "10.1", "comm": "2 runs, quick single turned into two."},
            {"ball": "9.6",  "comm": "Dot to end the over."},
        ],
    },
    "77777": {
        "series": "National One-Day Cup",
        "desc":   "Group A",
        "venue":  "M. A. Chidambaram Stadium, Chennai",
        "target": 0,  # first innings in progress — no target yet
        "innings": [
            {
                "team": "Rajasthan Royals", "score": 96, "wicket": 2, "over": 12.0,
                "batsman": {
                    "1": {"name": "Yashasvi Jaiswal", "run": 55, "ball": 38, "sr": 144.7},
                    "2": {"name": "Sanju Samson",      "run": 33, "ball": 25, "sr": 132.0},
                },
                "bolwer": {"1": {"name": "Trent Boult", "over": "3.0", "run": 22, "wicket": 1, "eco": 7.33}},
            },
        ],
        "second_team": "Delhi Capitals",
        "balls": [
            ["1","0","4","1","2","1"], ["0","4","1","1","6","0"], ["1","1","W","4","0","1"],
            ["4","1","2","0","1","6"], ["1","0","4","1","1","2"], ["0","6","1","4","W","1"],
            ["1","2","0","4","1","1"], ["4","0","1","6","1","0"], ["1","1","4","2","0","1"],
            ["6","1","0","4"],
        ],
        "commentary": [
            {"ball": "12.0", "comm": "FOUR to bring up the hundred stand approach."},
            {"ball": "11.5", "comm": "1 run, milked to deep point."},
            {"ball": "11.4", "comm": "SIX! Jaiswal stands tall and lofts it."},
        ],
    },
}


def _mock_match_for(endpoint: str) -> Dict[str, Any]:
    """
    Pick the catalog match whose id appears in the endpoint path
    (e.g. '/match/88888/scorecard'). Falls back to the first match.
    Also attaches a computed 'over_scripts' derived from that match's balls.
    """
    chosen_id = next(iter(_MOCK_MATCHES))
    for mid in _MOCK_MATCHES:
        if f"/{mid}/" in endpoint or endpoint.endswith(f"/{mid}"):
            chosen_id = mid
            break
    m = _MOCK_MATCHES[chosen_id]
    # target for run_need math: use the match target, else a nominal 200
    target = m.get("target") or 200
    m = {**m, "over_scripts": _build_over_scripts(m["balls"], target)}
    return m


# ═════════════════════════════════════════════════════════════════════════════
# Cricbuzz (cricbuzz-cricket.p.rapidapi.com) response adapters.
# Cricbuzz keys vary in case between endpoints (camelCase in /matches/v1/live,
# lowercase in /mcenter scard & overs), so we look up keys case-insensitively.
# Each adapter converts Cricbuzz JSON into the SAME internal shape the existing
# normalizer / match_service already consume — so nothing downstream changes.
# ═════════════════════════════════════════════════════════════════════════════

def _ci_get(d: dict, *names, default=None):
    """Case-insensitive dict lookup across several candidate key names."""
    if not isinstance(d, dict):
        return default
    lower_map = {k.lower(): v for k, v in d.items()}
    for n in names:
        if n.lower() in lower_map:
            return lower_map[n.lower()]
    return default


_CB_LIVE_KEYWORDS = ("in progress", "innings break", "rain", "delay", "tea", "lunch", "drinks")


def _adapt_cricbuzz_live_list(raw: dict) -> dict:
    """
    Convert Cricbuzz /matches/v1/live into {status, data:[ ... ]} where each item
    has the keys match_service expects: match_id, series, matchs, match_type,
    team_a/team_b, team_a_scores/team_a_over, team_b_scores/team_b_over,
    match_status, venue.
    """
    out = []
    type_matches = _ci_get(raw, "typeMatches", default=[]) or []
    for tm in type_matches:
        series_matches = _ci_get(tm, "seriesMatches", default=[]) or []
        for sm in series_matches:
            wrapper = _ci_get(sm, "seriesAdWrapper", default=None)
            if not wrapper:
                continue
            series_name = _ci_get(wrapper, "seriesName", default="")
            matches = _ci_get(wrapper, "matches", default=[]) or []
            for mt in matches:
                info = _ci_get(mt, "matchInfo", default={}) or {}
                score = _ci_get(mt, "matchScore", default={}) or {}

                team1 = _ci_get(info, "team1", default={}) or {}
                team2 = _ci_get(info, "team2", default={}) or {}
                venue = _ci_get(info, "venueInfo", default={}) or {}

                def _score_str(team_score_obj):
                    """Cricbuzz score obj → 'runs/wkts' + overs; handles multi-innings (Tests)."""
                    if not isinstance(team_score_obj, dict):
                        return "", ""
                    # pick the highest-numbered innings present (inngs1/inngs2/...)
                    inns = {k: v for k, v in team_score_obj.items() if isinstance(v, dict)}
                    if not inns:
                        return "", ""
                    # last innings wins (most recent)
                    last = list(inns.values())[-1]
                    runs = _ci_get(last, "runs", default=0)
                    wkts = _ci_get(last, "wickets", default=0)
                    ov = _ci_get(last, "overs", default="")
                    return f"{runs}/{wkts}", str(ov) if ov not in (None, "", 0) else ""

                a_score, a_over = _score_str(_ci_get(score, "team1Score", default={}))
                b_score, b_over = _score_str(_ci_get(score, "team2Score", default={}))

                out.append({
                    "match_id":     str(_ci_get(info, "matchId", default="")),
                    "series":       series_name,
                    "matchs":       _ci_get(info, "matchDesc", default=""),
                    "match_type":   _ci_get(info, "matchFormat", default="T20"),
                    "team_a":       _ci_get(team1, "teamName", default=""),
                    "team_b":       _ci_get(team2, "teamName", default=""),
                    "team_a_scores": a_score,
                    "team_a_over":   a_over,
                    "team_b_scores": b_score,
                    "team_b_over":   b_over,
                    # match_service filters on this; Cricbuzz uses state="In Progress"
                    "match_status": _ci_get(info, "state", default=""),
                    "venue":        (
                        f"{_ci_get(venue, 'ground', default='')}, {_ci_get(venue, 'city', default='')}".strip(", ")
                    ),
                })
    return {"status": True, "data": out}


def _adapt_cricbuzz_scorecard(raw: dict) -> dict:
    """
    Convert Cricbuzz /mcenter/v1/{id}/scard into the internal shape:
      {data: {scorecard: {"1": {team:{name,score,wicket,over,inning},
                                 batsman:{...}, bolwer:{...}}, ...}}}
    """
    innings_list = _ci_get(raw, "scoreCard", "scorecard", default=[]) or []
    scorecard = {}
    for inn in innings_list:
        inn_id = int(_ci_get(inn, "inningsId", "inningsid", default=len(scorecard) + 1) or (len(scorecard) + 1))
        team_name = _ci_get(inn, "batTeamName", "batteamname", default="Unknown")
        runs = _ci_get(inn, "score", default=0)
        wkts = _ci_get(inn, "wickets", default=0)
        overs = _ci_get(inn, "overs", default="0.0")

        # Some variants nest score under scoreDetails
        details = _ci_get(inn, "scoreDetails", default=None)
        if details:
            runs = _ci_get(details, "runs", default=runs)
            wkts = _ci_get(details, "wickets", default=wkts)
            overs = _ci_get(details, "overs", default=overs)

        # Batsmen → dict keyed by index (normalizer accepts dict or list)
        batsman_out = {}
        for i, b in enumerate(_ci_get(inn, "batsman", default=[]) or [], start=1):
            batsman_out[str(i)] = {
                "name": _ci_get(b, "name", default="Unknown"),
                "run":  _ci_get(b, "runs", default=0),
                "ball": _ci_get(b, "balls", default=0),
                "sr":   _ci_get(b, "strkrate", "strkRate", default=0),
            }
        bowler_out = {}
        for i, b in enumerate(_ci_get(inn, "bowler", default=[]) or [], start=1):
            bowler_out[str(i)] = {
                "name":   _ci_get(b, "name", default="Unknown"),
                "over":   _ci_get(b, "overs", default="0"),
                "run":    _ci_get(b, "runs", default=0),
                "wicket": _ci_get(b, "wickets", default=0),
                "eco":    _ci_get(b, "economy", default=0),
            }

        scorecard[str(inn_id)] = {
            "team": {
                "name":   team_name,
                "score":  runs,
                "wicket": wkts,
                "over":   overs,
                "inning": inn_id,
            },
            "batsman": batsman_out,
            "bolwer":  bowler_out,
        }
    return {"status": True, "data": {"scorecard": scorecard}}


def _parse_curovsstats(cur: str) -> list:
    """
    Turn Cricbuzz 'curovsstats' like '1 1 4 0 1 1  | 0 4 6 1 4 1' into a list of
    per-over ball lists: [['1','1','4','0','1','1'], ['0','4','6','1','4','1']].
    Tokens may include 'W' (wicket), 'wd'/'nb' (extras); we keep them as-is.
    """
    if not cur or not isinstance(cur, str):
        return []
    overs = []
    for chunk in cur.split("|"):
        balls = [t for t in chunk.strip().split() if t and t not in (".", "...")]
        if balls:
            overs.append(balls)
    return overs


def _adapt_cricbuzz_over_history(raw: dict) -> dict:
    """
    Convert Cricbuzz /mcenter/v1/{id}/overs into the internal overHistory shape:
      {data: {"<innings>": {"<idx>": {team:{over,cr_rate,rr_rate,run_need,ball_rem},
                                       overs:{"0":"1",...}}}}}
    Built from miniscore.curovsstats + chase metadata (target/crr/rrr/ballsrem).
    """
    mini = _ci_get(raw, "miniscore", default={}) or {}
    innings_id = int(_ci_get(mini, "inningsId", "inningsid", "inningsNbr", "inningsnbr", default=1) or 1)

    crr = float(_ci_get(mini, "crr", default=0.0) or 0.0)
    rrr = float(_ci_get(mini, "rrr", default=0.0) or 0.0)
    target = int(_ci_get(mini, "target", default=0) or 0)
    balls_rem = int(_ci_get(mini, "ballsrem", "ballsRem", default=0) or 0)
    overs_rem = float(_ci_get(mini, "oversrem", "oversRem", default=0.0) or 0.0)

    cur = _ci_get(mini, "curovsstats", "curOvsStats", default="") or ""
    over_lists = _parse_curovsstats(cur)

    # Current over number from the batting team's overs (e.g. 4.6)
    bat_score = _ci_get(mini, "batteamscore", "batTeamScore", default={}) or {}
    cur_runs = int(_ci_get(bat_score, "teamscore", "teamScore", default=0) or 0)

    # Determine the starting over number so the last chunk aligns to "now".
    # inningsscores gives the current overs figure.
    inn_scores = _ci_get(mini, "inningsscores", "inningsScores", default={}) or {}
    inn_list = _ci_get(inn_scores, "inningsscore", "inningsScore", default=[]) or []
    cur_over_val = 0.0
    if inn_list:
        cur_over_val = float(_ci_get(inn_list[-1], "overs", default=0.0) or 0.0)

    # Derive innings length (max overs) from the live feed: balls_bowled + balls_rem.
    # Format-agnostic and exact (120 balls T20, 300 balls ODI).
    _cur_completed = int(cur_over_val)
    _cur_balls_in_over = round((cur_over_val - _cur_completed) * 10)
    _balls_bowled = _cur_completed * 6 + _cur_balls_in_over
    max_overs = 0
    if balls_rem > 0:
        max_overs = round((_balls_bowled + balls_rem) / 6)
    elif overs_rem > 0:
        max_overs = round(cur_over_val + overs_rem)
    if 18 <= max_overs <= 22:
        max_overs = 20
    elif 45 <= max_overs <= 55:
        max_overs = 50

    n_overs = len(over_lists)
    # The curovsstats holds the most recent N overs; the last one is the
    # current over. Compute the over number of the FIRST chunk.
    completed_now = int(cur_over_val)  # floor of current overs
    start_over = max(1, completed_now - n_overs + 1)

    innings_data = {}
    running_runs = 0
    for idx, balls in enumerate(over_lists):
        ov_num = start_over + idx
        for b in balls:
            if b.isdigit():
                running_runs += int(b)
        run_need = max(0, target - cur_runs) if target else 0
        this_ball_rem = balls_rem if idx == n_overs - 1 else max(0, balls_rem + (n_overs - 1 - idx) * 6)
        innings_data[str(idx)] = {
            "team": {
                "over":     ov_num,
                "cr_rate":  crr,
                "rr_rate":  rrr,
                "run_need": run_need,
                "ball_rem": this_ball_rem,
            },
            "overs": {str(bi): ball for bi, ball in enumerate(balls)},
        }

    if not innings_data:
        return {"status": True, "data": {"_meta": {"max_overs": max_overs}}}
    return {"status": True, "data": {str(innings_id): innings_data, "_meta": {"max_overs": max_overs}}}


def _adapt_cricbuzz_commentary(raw: dict) -> dict:
    """
    Convert Cricbuzz /mcenter/v1/{id}/comm into the internal commentary shape:
      {data: {commentary: [{ball: "15.4", comm: "..."}]}}
    Used only as a fallback ball source, so best-effort.
    """
    out = []
    comm_list = _ci_get(raw, "commentaryList", "comwrapper", "commentarylist", default=[]) or []
    for c in comm_list:
        if not isinstance(c, dict):
            continue
        over = _ci_get(c, "overNumber", "overnumber", "overNum", default=None)
        text = _ci_get(c, "commText", "commtext", "comm", default="")
        if over is not None:
            out.append({"ball": str(over), "comm": str(text)})
    return {"status": True, "data": {"commentary": out}}


class LiveAPIClient:
    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY")
        self.host = os.getenv("RAPIDAPI_HOST", "cricbuzz-cricket.p.rapidapi.com")
        self.base_url = f"https://{self.host}"
        
        if not self.api_key:
            logger.warning("RAPIDAPI_KEY is not set. Live API calls will fail.")

    def _get_headers(self):
        return {
            "x-rapidapi-host": self.host,
            "x-rapidapi-key": self.api_key
        }

    def _make_request(self, endpoint: str) -> Any:
        if not self.api_key:
            # No key configured → serve populated mock data so the whole live
            # feature works in development / offline demo mode instead of 500ing.
            logger.warning(f"RAPIDAPI_KEY missing; serving mock data for {endpoint}.")
            return self._get_mock_data(endpoint)

        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code == 429:
                logger.error("RapidAPI Rate Limit Exceeded. Falling back to mock data.")
                return self._get_mock_data(endpoint)
                
            response.raise_for_status()
            
            data = response.json()
            
            # The API often returns 200 OK but sets status: False when data is missing
            if isinstance(data, dict) and data.get("status") is False:
                msg = data.get("msg") or data.get("message") or "API returned status: False (No Data)"
                logger.error(f"RapidAPI Logical Error: {msg}")
                return self._get_mock_data(endpoint)
                
            return data
            
        except (requests.exceptions.Timeout, requests.exceptions.HTTPError, requests.exceptions.RequestException, ValueError) as e:
            logger.error(f"RapidAPI Error: {e}. Falling back to mock data.")
            return self._get_mock_data(endpoint)

    def _get_mock_data(self, endpoint: str) -> Any:
        """
        Provides mock data when the API limit is exceeded so the UI doesn't break.

        All structures match the exact schema the normalizer expects:
          - scorecard:   data.scorecard["1"] / ["2"]  with team{name,score,wicket,over} +
                         batsman{} dict + bolwer{} dict
          - overHistory: data["1"][over_idx]{team:{over,cr_rate,rr_rate,...}, overs:{"0":"1",...}}
          - liveMatches: data[] with match_id, series, matchs, match_type, team_a/b, match_status, venue
        """
        if endpoint == "/liveMatches":
            # Build the list straight from the catalog so scores are ALWAYS
            # present (the frontend list cards must never show a bare "-").
            data = []
            for mid, m in _MOCK_MATCHES.items():
                inn1 = m["innings"][0]
                inn2 = m["innings"][1] if len(m["innings"]) > 1 else None
                data.append({
                    "match_id":     mid,
                    "series":       m["series"],
                    "matchs":       m["desc"],
                    "match_type":   "T20",
                    "team_a":       inn1["team"],
                    "team_b":       inn2["team"] if inn2 else m.get("second_team", "Opponent"),
                    # Scores included directly so list cards are populated even
                    # before the per-match scorecard enrichment runs.
                    "team_a_scores": f"{inn1['score']}/{inn1['wicket']}",
                    "team_a_over":   str(inn1["over"]),
                    "team_b_scores": (f"{inn2['score']}/{inn2['wicket']}" if inn2 else "Yet to bat"),
                    "team_b_over":   (str(inn2["over"]) if inn2 else ""),
                    "match_status": "Live - In Progress",
                    "venue":        m["venue"],
                })
            return {"status": True, "data": data}

        elif "scorecard" in endpoint:
            m = _mock_match_for(endpoint)
            scorecard = {}
            for i, inn in enumerate(m["innings"], start=1):
                scorecard[str(i)] = {
                    "team": {
                        "name":   inn["team"],
                        "score":  inn["score"],
                        "wicket": inn["wicket"],
                        "over":   inn["over"],
                        "inning": i,
                    },
                    "batsman": inn.get("batsman", {}),
                    "bolwer":  inn.get("bolwer", {}),
                }
            return {"status": True, "data": {"scorecard": scorecard}}

        elif "overHistory" in endpoint:
            m = _mock_match_for(endpoint)
            # The chase (2nd) innings drives the ball-by-ball history; if only
            # one innings exists, use it as innings 1.
            active_idx = 2 if len(m["innings"]) > 1 else 1
            over_scripts = m["over_scripts"]
            innings_data = {}
            for idx, (ov_num, balls, cr_rate, run_need, ball_rem) in enumerate(over_scripts):
                innings_data[str(idx)] = {
                    "team": {
                        "over":     ov_num,
                        "cr_rate":  cr_rate,
                        "rr_rate":  round(run_need / ball_rem * 6, 2) if ball_rem > 0 else 0,
                        "run_need": run_need,
                        "ball_rem": ball_rem,
                    },
                    "overs": {str(b_idx): ball for b_idx, ball in enumerate(balls)},
                }
            return {"status": True, "data": {str(active_idx): innings_data}}

        elif "commentary" in endpoint:
            m = _mock_match_for(endpoint)
            return {"status": True, "data": {"commentary": m["commentary"]}}

        return {"status": False, "msg": "Mock Not Implemented"}

    def get_live_matches(self) -> Dict[str, Any]:
        """Fetches the list of live matches from Cricbuzz, adapted to internal shape."""
        if not self.api_key:
            return self._get_mock_data("/liveMatches")
        raw = self._raw_request("/matches/v1/live")
        if raw is None:
            # Hard failure → let the service layer fall back to mock
            return self._get_mock_data("/liveMatches")
        return _adapt_cricbuzz_live_list(raw)

    def _raw_request(self, endpoint: str):
        """
        Perform a raw GET against the configured RapidAPI host and return the
        parsed JSON dict, or None on any failure (caller decides fallback).
        Unlike _make_request, this does NOT reshape or auto-mock.
        """
        if not self.api_key:
            return None
        url = f"{self.base_url}{endpoint}"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=10)
            if resp.status_code == 429:
                logger.error("RapidAPI rate limit hit (429).")
                return None
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, dict) else None
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.error(f"Cricbuzz request failed for {endpoint}: {e}")
            return None

    def get_mock_live_matches(self) -> Dict[str, Any]:
        """
        Public accessor for the mock live-match list. Used by the service layer
        as a graceful fallback when the real provider returns no live matches
        (or the API key is missing / the call fails), so the UI is never empty.
        """
        return self._get_mock_data("/liveMatches")

    def get_scorecard(self, match_id: str) -> Dict[str, Any]:
        """Fetches full scorecard for a specific match, adapted to internal shape."""
        # No key → mock
        if not self.api_key:
            return self._get_mock_data(f"/match/{match_id}/scorecard")
        raw = self._raw_request(f"/mcenter/v1/{match_id}/scard")
        if raw is None:
            return self._get_mock_data(f"/match/{match_id}/scorecard")
        return _adapt_cricbuzz_scorecard(raw)

    def get_commentary(self, match_id: str) -> Dict[str, Any]:
        """Fetches commentary for a match, adapted to internal shape."""
        if not self.api_key:
            return self._get_mock_data(f"/match/{match_id}/commentary")
        raw = self._raw_request(f"/mcenter/v1/{match_id}/comm")
        if raw is None:
            return self._get_mock_data(f"/match/{match_id}/commentary")
        return _adapt_cricbuzz_commentary(raw)

    def get_over_history(self, match_id: str) -> Dict[str, Any]:
        """
        Fetches over-by-over ball history for a match, adapted to internal shape.
        Cricbuzz exposes recent balls via /mcenter/v1/{id}/overs → miniscore.curovsstats.
        """
        if not self.api_key:
            return self._get_mock_data(f"/match/{match_id}/overHistory")
        raw = self._raw_request(f"/mcenter/v1/{match_id}/overs")
        if raw is None:
            return self._get_mock_data(f"/match/{match_id}/overHistory")
        return _adapt_cricbuzz_over_history(raw)
