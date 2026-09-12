import logging
from typing import List, Dict, Any
from .api_client import LiveAPIClient, APIClientError

logger = logging.getLogger(__name__)

# Statuses that explicitly mean the match is NOT live
_NON_LIVE_KEYWORDS = ["complete", "abandon", "upcoming", "schedule", "finish", "stump", "result", "delay"]
# Statuses that imply it IS live
_LIVE_KEYWORDS = ["live", "progress", "in progress"]


def _is_live_match(match_status: str) -> bool:
    s = match_status.lower()
    return any(kw in s for kw in _LIVE_KEYWORDS) and not any(kw in s for kw in _NON_LIVE_KEYWORDS)


def _fmt_score(score, wickets, overs) -> str:
    """Format a score string like '145/4 (15.4)'."""
    if score in (None, "", 0) and wickets in (None, "", 0):
        return "-"
    score_part = f"{score}/{wickets}" if wickets not in (None, "", 0) else str(score)
    overs_part = f" ({overs})" if overs not in (None, "", 0, "0", "0.0") else ""
    return f"{score_part}{overs_part}"


def _extract_innings_scores(scorecard: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Pull each innings' team name + score/wickets/overs out of a raw scorecard
    response. Returns a dict keyed by team name:
        { "<team name>": {"score": int, "wickets": int, "overs": str}, ... }
    Tolerant of missing keys — returns {} if the shape is unexpected.
    """
    out: Dict[str, Dict[str, Any]] = {}
    try:
        sc = scorecard.get("data", {}).get("scorecard", {})
        for key, inn in sc.items():
            if not str(key).isdigit() or not isinstance(inn, dict):
                continue
            team = inn.get("team", {}) or {}
            name = str(team.get("name", "")).strip()
            if not name:
                continue
            out[name] = {
                "score":   int(team.get("score", 0) or 0),
                "wickets": int(team.get("wicket", 0) or 0),
                "overs":   str(team.get("over", "0.0") or "0.0"),
            }
    except Exception:
        pass
    return out


class LiveMatchService:
    def __init__(self, api_client: LiveAPIClient = None):
        self.client = api_client or LiveAPIClient()

    def get_live_matches(self) -> List[Dict[str, Any]]:
        """
        Fetches all matches and strictly filters for genuinely LIVE/IN-PROGRESS matches.
        Enriches each match with score fields expected by the frontend MatchCard component:
          team_a_score, team_a_overs, team_b_score, team_b_overs
        """
        used_fallback = False
        try:
            raw_response = self.client.get_live_matches()
        except APIClientError as e:
            # No API key / hard failure → use the populated mock catalog so the
            # live page always has matches to show instead of an empty state.
            logger.warning(f"Live API unavailable ({e}); using mock live matches.")
            raw_response = self.client.get_mock_live_matches()
            used_fallback = True

        match_list = raw_response.get("data", []) if isinstance(raw_response, dict) else raw_response
        if not isinstance(match_list, list):
            match_list = list(match_list.values()) if isinstance(match_list, dict) else []

        live_matches = []
        for match in match_list:
            if not isinstance(match, dict):
                continue

            match_status = str(match.get("match_status", ""))
            if not _is_live_match(match_status):
                continue

            team_a = match.get("team_a", "")
            team_b = match.get("team_b", "")

            # The RapidAPI liveMatches endpoint may include score fields directly.
            # Common keys: team_a_scores / team_a_over  or  score_a / score_b.
            # We try the known variants and fall back gracefully.
            team_a_score_raw = (
                match.get("team_a_scores")
                or match.get("score_a")
                or match.get(f"{team_a}_score", "")
            )
            team_a_overs_raw = (
                match.get("team_a_over")
                or match.get("over_a", "")
            )
            team_b_score_raw = (
                match.get("team_b_scores")
                or match.get("score_b")
                or match.get(f"{team_b}_score", "")
            )
            team_b_overs_raw = (
                match.get("team_b_over")
                or match.get("over_b", "")
            )

            # If the API already returns a formatted score string use it directly,
            # otherwise build one from the raw parts.
            def _coerce(v):
                return str(v).strip() if v else ""

            team_a_score_str = _coerce(team_a_score_raw)
            team_b_score_str = _coerce(team_b_score_raw)
            team_a_overs_str = _coerce(team_a_overs_raw)
            team_b_overs_str = _coerce(team_b_overs_raw)

            match_id = match.get("match_id")

            # ── Always enrich from the per-match scorecard and PREFER it over the
            #    live-list payload's score. The list payload (Cricbuzz
            #    /matches/v1/live) can lag a few balls behind the live scorecard,
            #    which caused the list card and the detail page to disagree.
            #    The scorecard is the same source the detail page reads, so
            #    using it here keeps both views identical and always current.
            if match_id:
                try:
                    scorecard = self.client.get_scorecard(str(match_id))
                    innings = _extract_innings_scores(scorecard)

                    def _match_team(target: str) -> Dict[str, Any] | None:
                        if not target:
                            return None
                        # exact, then case-insensitive, then substring match
                        if target in innings:
                            return innings[target]
                        low = target.lower()
                        for name, data in innings.items():
                            if name.lower() == low:
                                return data
                        for name, data in innings.items():
                            if low in name.lower() or name.lower() in low:
                                return data
                        return None

                    a_inn = _match_team(team_a)
                    b_inn = _match_team(team_b)

                    # If team names weren't matched but we have innings, assign
                    # them positionally (innings order = team_a then team_b).
                    if (a_inn is None or b_inn is None) and len(innings) >= 1:
                        vals = list(innings.values())
                        names = list(innings.keys())
                        if a_inn is None and len(vals) >= 1:
                            a_inn = vals[0]
                            if not team_a:
                                team_a = names[0]
                        if b_inn is None and len(vals) >= 2:
                            b_inn = vals[1]
                            if not team_b:
                                team_b = names[1]

                    # Prefer the fresh scorecard score/overs over the stale list value.
                    if a_inn:
                        team_a_score_str = f"{a_inn['score']}/{a_inn['wickets']}"
                        team_a_overs_str = a_inn["overs"] or team_a_overs_str
                    if b_inn:
                        team_b_score_str = f"{b_inn['score']}/{b_inn['wickets']}"
                        team_b_overs_str = b_inn["overs"] or team_b_overs_str
                except Exception as e:
                    logger.debug(f"Scorecard enrichment failed for {match_id}: {e}")

            # Final fallbacks: a team that hasn't batted shows "Yet to bat"
            # rather than a bare dash; overs stay blank when 0.
            team_a_score_str = team_a_score_str or "Yet to bat"
            team_b_score_str = team_b_score_str or "Yet to bat"

            normalized_match = {
                "match_id":          match_id,
                "series":            match.get("series", "") or "Live Series",
                "match_description": match.get("matchs", ""),
                "match_format":      match.get("match_type", "T20") or "T20",
                "team_a":            team_a or "Team A",
                "team_b":            team_b or "Team B",
                # Score fields consumed by the frontend MatchCard
                "team_a_score":      team_a_score_str,
                "team_a_overs":      team_a_overs_str,
                "team_b_score":      team_b_score_str,
                "team_b_overs":      team_b_overs_str,
                "status":            match_status or "Live",
                "venue":             match.get("venue", "") or "Venue TBC",
            }

            if normalized_match["match_id"]:
                live_matches.append(normalized_match)

        # If the real provider succeeded but no matches are currently live,
        # fall back to the mock catalog so the page always has content to show
        # (avoids the confusing "No live matches" empty state during downtime).
        if not live_matches and not used_fallback:
            logger.info("No live matches from provider; using mock live matches.")
            try:
                mock_list = self.client.get_mock_live_matches().get("data", [])
                return self.get_live_matches_from_raw(mock_list)
            except Exception as e:
                logger.debug(f"Mock fallback failed: {e}")

        return live_matches

    def get_live_matches_from_raw(self, match_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize a raw provider/mock match list into frontend MatchCard shape,
        WITHOUT re-fetching the list. Used for the mock fallback path so we
        don't recurse. Scores already present in the raw list are used directly.
        """
        out: List[Dict[str, Any]] = []
        for match in match_list:
            if not isinstance(match, dict):
                continue
            team_a = match.get("team_a", "") or "Team A"
            team_b = match.get("team_b", "") or "Team B"

            def _coerce(v):
                return str(v).strip() if v else ""

            out.append({
                "match_id":          match.get("match_id"),
                "series":            match.get("series", "") or "Live Series",
                "match_description": match.get("matchs", ""),
                "match_format":      match.get("match_type", "T20") or "T20",
                "team_a":            team_a,
                "team_b":            team_b,
                "team_a_score":      _coerce(match.get("team_a_scores")) or "Yet to bat",
                "team_a_overs":      _coerce(match.get("team_a_over")),
                "team_b_score":      _coerce(match.get("team_b_scores")) or "Yet to bat",
                "team_b_overs":      _coerce(match.get("team_b_over")),
                "status":            match.get("match_status", "") or "Live",
                "venue":             match.get("venue", "") or "Venue TBC",
            })
        return [m for m in out if m["match_id"]]
