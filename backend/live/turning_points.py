"""
Shared turning-point reason generator.

Previously this identical heuristic was copy-pasted in:
  - backend/routes/historical.py
  - backend/live/intelligence.py

Single source of truth lives here.
"""

from typing import Optional


def build_turning_point_reason(
    *,
    new_label: str,
    prev_label: str,
    batting_team: str,
    bowling_team: str,
    runs_last_12: int = 0,
    wickets_last_12: int = 0,
    dot_balls_last_12: int = 0,
    boundaries_last_12: int = 0,
) -> str:
    """
    Produce a human-readable, AI-driven explanation for a momentum shift.
    """
    if wickets_last_12 >= 2:
        return (
            f"Wicket collapse! {bowling_team} took {wickets_last_12} quick wickets "
            f"in the last 12 balls, triggering a major momentum shift to {new_label}."
        )
    elif wickets_last_12 == 1:
        if new_label == "Negative":
            return (
                f"Crucial breakthrough by {bowling_team}! A key wicket and "
                f"{dot_balls_last_12} dot balls swung momentum to {bowling_team}."
            )
        else:
            return (
                f"Important wicket fell for {batting_team}, shifting match dynamics "
                f"from {prev_label} to {new_label}."
            )
    elif runs_last_12 >= 18 or boundaries_last_12 >= 3:
        return (
            f"Aggressive boundary surge by {batting_team}! "
            f"Scored {runs_last_12} runs ({boundaries_last_12} boundaries) in the last 12 balls, "
            f"boosting momentum to {new_label}."
        )
    elif runs_last_12 >= 12:
        return (
            f"Scoring acceleration by {batting_team}! "
            f"{runs_last_12} runs off the last 12 deliveries shifted momentum from {prev_label} to {new_label}."
        )
    elif dot_balls_last_12 >= 7:
        return (
            f"Disciplined bowling spell by {bowling_team}! "
            f"Mounted pressure with {dot_balls_last_12} dot balls out of 12."
        )
    elif new_label == "Positive" and prev_label == "Negative":
        return (
            f"Major counter-attack by {batting_team} completely reversed the momentum "
            f"from Negative to Positive."
        )
    elif new_label == "Negative" and prev_label == "Positive":
        return (
            f"{bowling_team} applied heavy pressure to halt {batting_team}'s scoring spree, "
            f"reversing momentum to Negative."
        )

    return f"Match state evolved — momentum transitioned from {prev_label} to {new_label}."

