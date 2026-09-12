"""
Sample Match Data Generator
=============================
Generates a realistic T20 cricket match dataset in CSV format.
This script creates a complete ball-by-ball record for a dramatic
T20 match between two teams, suitable for testing the analytics engine.

Run this script standalone to regenerate the sample data:
    python generate_sample_data.py
"""

import pandas as pd
import numpy as np
import random
import os

random.seed(42)
np.random.seed(42)

# ── Team Config ────────────────────────────────────────────────
TEAM_A = "Mumbai Titans"
TEAM_B = "Delhi Strikers"

TEAM_A_BATSMEN = [
    "R. Sharma", "V. Kohli", "S. Iyer", "H. Pandya",
    "K. Pollard", "I. Kishan", "K. Ahmed", "R. Chahar",
    "J. Bumrah", "T. Boult", "P. Chawla"
]

TEAM_B_BATSMEN = [
    "S. Dhawan", "P. Shaw", "R. Pant", "M. Stoinis",
    "S. Hetmyer", "A. Patel", "R. Ashwin", "K. Rabada",
    "A. Nortje", "I. Sharma", "P. Dubey"
]

TEAM_A_BOWLERS = ["J. Bumrah", "T. Boult", "R. Chahar", "K. Ahmed", "P. Chawla"]
TEAM_B_BOWLERS = ["K. Rabada", "A. Nortje", "I. Sharma", "R. Ashwin", "P. Dubey"]

DISMISSAL_TYPES = ["bowled", "caught", "lbw", "run out", "stumped", "caught & bowled"]


def generate_ball(over, ball, batting_team, bowling_team, batsmen, bowlers,
                  batsman_idx, wickets, phase="middle", pressure=0.5):
    """Generate a single ball delivery with realistic outcomes."""

    bowler = random.choice(bowlers)
    batsman = batsmen[min(batsman_idx, len(batsmen) - 1)]

    # Base probabilities adjusted by phase and pressure
    if phase == "powerplay":
        # More boundaries, fewer dots
        probs = {0: 0.30, 1: 0.28, 2: 0.10, 3: 0.02, 4: 0.18, 6: 0.07}
        wicket_prob = 0.04
        extras_prob = 0.06
    elif phase == "death":
        # High scoring, more boundaries, more wickets
        probs = {0: 0.22, 1: 0.22, 2: 0.08, 3: 0.03, 4: 0.22, 6: 0.13}
        wicket_prob = 0.07
        extras_prob = 0.08
    else:
        # Middle overs: balanced
        probs = {0: 0.38, 1: 0.28, 2: 0.08, 3: 0.01, 4: 0.14, 6: 0.05}
        wicket_prob = 0.05
        extras_prob = 0.05

    # Pressure adjustment
    wicket_prob += pressure * 0.03
    probs[0] += pressure * 0.05
    probs[4] -= pressure * 0.03
    probs[6] -= pressure * 0.02

    # Normalize probabilities
    total_p = sum(probs.values())
    probs = {k: v / total_p for k, v in probs.items()}

    # Determine runs off bat
    runs_off_bat = random.choices(list(probs.keys()), weights=list(probs.values()), k=1)[0]

    # Extras
    extras = 0
    if random.random() < extras_prob:
        extras = random.choices([1, 2, 4, 5], weights=[0.6, 0.2, 0.1, 0.1], k=1)[0]

    total_runs = runs_off_bat + extras

    # Wicket
    is_wicket = 0
    dismissal_kind = ""
    player_dismissed = ""
    if random.random() < wicket_prob and wickets < 10:
        is_wicket = 1
        dismissal_kind = random.choice(DISMISSAL_TYPES)
        player_dismissed = batsman
        if runs_off_bat > 0 and dismissal_kind != "run out":
            runs_off_bat = 0
            total_runs = extras

    return {
        "match_id": 1,
        "innings": 0,  # Set later
        "over": over,
        "ball": ball,
        "batting_team": batting_team,
        "bowling_team": bowling_team,
        "batsman": batsman,
        "bowler": bowler,
        "runs_off_bat": runs_off_bat,
        "extras": extras,
        "total_runs": total_runs,
        "is_wicket": is_wicket,
        "dismissal_kind": dismissal_kind,
        "player_dismissed": player_dismissed
    }


def generate_innings(innings_num, batting_team, bowling_team, batsmen, bowlers,
                     target=None):
    """Generate a complete innings with realistic T20 flow."""
    balls = []
    wickets = 0
    batsman_idx = 0
    total_score = 0

    for over in range(20):
        if wickets >= 10:
            break

        # Determine phase
        if over < 6:
            phase = "powerplay"
        elif over >= 16:
            phase = "death"
        else:
            phase = "middle"

        # Create dramatic scenarios
        pressure = 0.5
        if target is not None:
            balls_remaining = (20 - over) * 6
            runs_needed = target - total_score
            if balls_remaining > 0:
                rrr = runs_needed / (balls_remaining / 6)
                if rrr > 12:
                    pressure = 0.8
                elif rrr > 10:
                    pressure = 0.65
                elif rrr < 6:
                    pressure = 0.3

        # Add dramatic moments - specific overs with unusual action
        if innings_num == 1:
            # Big over for Team A around over 14-15
            if over in [14, 15]:
                pressure = 0.2  # Lower pressure = more runs
            # Tight spell around over 8-10
            if over in [8, 9]:
                pressure = 0.7
        else:
            # Team B starts strong
            if over in [3, 4]:
                pressure = 0.25
            # Mid-innings collapse around overs 10-12
            if over in [10, 11]:
                pressure = 0.85
            # Death over recovery/drama
            if over in [17, 18]:
                pressure = 0.35
            if over == 19:
                pressure = 0.5

        for ball_num in range(1, 7):
            if wickets >= 10:
                break

            delivery = generate_ball(
                over, ball_num, batting_team, bowling_team,
                batsmen, bowlers, batsman_idx, wickets,
                phase=phase, pressure=pressure
            )
            delivery["innings"] = innings_num
            balls.append(delivery)

            total_score += delivery["total_runs"]
            if delivery["is_wicket"]:
                wickets += 1
                batsman_idx += 1

            # Check if target chased
            if target is not None and total_score >= target:
                break

        if target is not None and total_score >= target:
            break

    return balls, total_score, wickets


def generate_match():
    """Generate a complete T20 match between two teams."""

    # First innings: Team A bats
    innings1_balls, score1, wickets1 = generate_innings(
        1, TEAM_A, TEAM_B, TEAM_A_BATSMEN, TEAM_B_BOWLERS
    )

    # Second innings: Team B chases
    target = score1 + 1
    innings2_balls, score2, wickets2 = generate_innings(
        2, TEAM_B, TEAM_A, TEAM_B_BATSMEN, TEAM_A_BOWLERS,
        target=target
    )

    all_balls = innings1_balls + innings2_balls
    df = pd.DataFrame(all_balls)

    return df


if __name__ == "__main__":
    df = generate_match()

    # Save to data directory
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    filepath = os.path.join(data_dir, "sample_match.csv")
    df.to_csv(filepath, index=False)

    print(f"✓ Generated sample match data: {filepath}")
    print(f"  Total deliveries: {len(df)}")

    # Print summary
    for innings in [1, 2]:
        inn_df = df[df["innings"] == innings]
        team = inn_df["batting_team"].iloc[0]
        runs = inn_df["total_runs"].sum()
        wickets = inn_df["is_wicket"].sum()
        overs = f"{inn_df['over'].iloc[-1]}.{inn_df['ball'].iloc[-1]}"
        print(f"  Innings {innings}: {team} - {runs}/{wickets} ({overs} overs)")
