"""
AI Contextual Commentary Engine
Synthesizes ML predictions, win probability swings, and SHAP feature importances
into broadcast-grade analytical commentary and tactical insights.
"""

from typing import Dict, Any, List, Optional


class AICommentaryEngine:
    """Generates broadcast-style narrative commentary and tactical insights."""

    # Human-friendly feature mappings
    FEATURE_EXPLANATIONS = {
        "pressure_index": "escalating dot-ball pressure and required run rate squeeze",
        "required_run_rate": "steep required run rate mounting above comfort zones",
        "current_run_rate": "accelerating scoring tempo and boundary conversion",
        "runs_last_6_balls": "short-term scoring momentum and boundary intent",
        "runs_last_12_balls": "sustained multi-over scoring acceleration",
        "runs_last_30_balls": "dominance through the middle phase",
        "wickets_last_n": "cluster of quick dismissals crippling batting depth",
        "current_wickets": "top-order vulnerability and depleted batting resources",
        "dot_balls_last_12_balls": "string of scoreless deliveries drying up boundaries",
        "dot_ball_pct": "high proportion of dot balls stifling chase momentum",
        "boundary_freq": "frequent boundary hits shifting win probability",
        "run_rate_acceleration": "sharp run-rate spike breaking bowler rhythm",
    }

    def generate_commentary(
        self,
        batting_team: str,
        bowling_team: str,
        current_over: int,
        current_ball: int,
        current_score: int,
        current_wickets: int,
        target: Optional[int] = None,
        win_prob_batting: float = 50.0,
        win_prob_delta: float = 0.0,
        momentum_label: str = "Neutral",
        batter_name: Optional[str] = None,
        bowler_name: Optional[str] = None,
        top_shap_features: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generates structured narrative commentary."""
        over_str = f"{current_over}.{current_ball}"
        crr = round((current_score / max(1, current_over * 6 + current_ball)) * 6, 2)
        
        # Calculate RRR if 2nd innings
        rrr = 0.0
        balls_remaining = max(0, 120 - (current_over * 6 + current_ball))
        runs_needed = 0
        if target and target > 0:
            runs_needed = max(0, target - current_score)
            if balls_remaining > 0:
                rrr = round((runs_needed / balls_remaining) * 6, 2)

        # Determine dominant SHAP drivers
        top_factors = []
        if top_shap_features:
            for feat in top_shap_features[:3]:
                feat_clean = feat.lower().strip()
                if feat_clean in self.FEATURE_EXPLANATIONS:
                    top_factors.append(self.FEATURE_EXPLANATIONS[feat_clean])
        
        if not top_factors:
            if target and rrr > 11.0:
                top_factors.append("steep required run rate mounting above comfort zones")
            elif current_wickets >= 5:
                top_factors.append("top-order collapse putting pressure on tailenders")
            else:
                top_factors.append("phase-specific resource utilization")

        primary_factor = top_factors[0]

        # Calculate leverage / impact rating (1 - 10)
        abs_delta = abs(win_prob_delta)
        if abs_delta >= 25.0:
            impact_rating = 10
            tone = "CRITICAL"
        elif abs_delta >= 15.0:
            impact_rating = 8
            tone = "MOMENTUM_SHIFT"
        elif rrr > 13.0 or current_wickets >= 7:
            impact_rating = 7
            tone = "TACTICAL_PRESSURE"
        elif win_prob_batting >= 75.0 or win_prob_batting <= 25.0:
            impact_rating = 6
            tone = "DOMINANT"
        else:
            impact_rating = 5
            tone = "BALANCED"

        # Build Headline
        batter_mention = f" ({batter_name})" if batter_name else ""
        bowler_mention = f" ({bowler_name})" if bowler_name else ""

        if tone == "CRITICAL":
            headline = f"CRITICAL MATCH PIVOT: {bowling_team if win_prob_delta < 0 else batting_team} seize massive leverage at {over_str} ov!"
        elif tone == "MOMENTUM_SHIFT":
            headline = f"MOMENTUM SWING: {batting_team if win_prob_batting > 50 else bowling_team} gain upper hand driven by {primary_factor}."
        elif tone == "TACTICAL_PRESSURE":
            headline = f"PRESSURE APPLIED: Required Rate climbs to {rrr} RPO as {bowling_team} tighten field."
        elif tone == "DOMINANT":
            leader = batting_team if win_prob_batting > 50 else bowling_team
            headline = f"COMMANDING POSITION: {leader} in firm control with {win_prob_batting if win_prob_batting > 50 else 100 - win_prob_batting:.0f}% win probability."
        else:
            headline = f"BALANCED CONTEST: {batting_team} {current_score}/{current_wickets} at {over_str} ov in tense tactical battle."

        # Narrative commentary synthesis
        paragraphs = []
        if target:
            chase_context = f"Chasing {target}, {batting_team} stand at {current_score}/{current_wickets} after {over_str} overs, needing {runs_needed} runs from {balls_remaining} balls (RRR: {rrr} RPO)."
        else:
            chase_context = f"Batting first, {batting_team} have reached {current_score}/{current_wickets} after {over_str} overs at a Current Run Rate of {crr} RPO."

        ml_insight = f"Our win prediction engine evaluates {batting_team}'s win probability at {win_prob_batting:.1f}% ({'+' if win_prob_delta >= 0 else ''}{win_prob_delta:.1f}% shift)."
        
        driver_context = f"Key statistical drivers highlight {', '.join(top_factors)}, reflecting a {momentum_label.lower()} momentum state."
        if batter_mention or bowler_mention:
            player_context = f"The battle between striker{batter_mention} and bowler{bowler_mention} is proving decisive for the remaining phase."
        else:
            player_context = ""

        commentary_text = f"{chase_context} {ml_insight} {driver_context} {player_context}".strip()

        # Tactical recommendation
        if target and rrr > 11.0:
            tactical = f"{batting_team} must target boundary releases in the next 12 deliveries and exploit matchups against boundary riders, while {bowling_team} should bowl hard lengths into the pitch."
        elif current_wickets <= 3 and current_over < 15:
            tactical = f"With wickets in hand, {batting_team} are well-positioned to launch an aggressive assault in the death overs. {bowling_team} need wicket-taking variations."
        elif win_prob_batting > 75.0:
            tactical = f"{batting_team} should minimize high-risk dismissals and focus on calculated singles and doubles to easily cross the line."
        else:
            tactical = f"Both captains face a critical phase: protecting bowling options while maintaining scoreboard pressure will dictate the final outcome."

        return {
            "headline": headline,
            "commentary": commentary_text,
            "tactical_insight": tactical,
            "primary_driver": primary_factor,
            "tone": tone,
            "impact_rating": impact_rating,
            "win_probability_batting": win_prob_batting,
            "momentum_label": momentum_label,
        }


commentary_engine = AICommentaryEngine()
