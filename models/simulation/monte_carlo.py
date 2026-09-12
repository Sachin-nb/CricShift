"""
Monte Carlo Match Simulator Engine
Provides stochastic ball-by-ball match simulations and probability distribution curves.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional


class MonteCarloSimulator:
    """Stochastic ball-by-ball Monte Carlo simulator for cricket match states."""

    # Base transition distributions per phase: [0, 1, 2, 3, 4, 6, Wicket]
    PHASE_BASE_PROBS = {
        "powerplay": {
            0: 0.44, 1: 0.26, 2: 0.05, 3: 0.01, 4: 0.15, 6: 0.05, "W": 0.04
        },
        "middle": {
            0: 0.35, 1: 0.40, 2: 0.08, 3: 0.01, 4: 0.10, 6: 0.03, "W": 0.03
        },
        "death": {
            0: 0.25, 1: 0.24, 2: 0.10, 3: 0.02, 4: 0.20, 6: 0.11, "W": 0.08
        },
    }

    def __init__(self, player_stats_df: Optional[pd.DataFrame] = None):
        self.player_stats = player_stats_df

    def _get_player_modifiers(self, batter_name: Optional[str], bowler_name: Optional[str]) -> Dict[str, float]:
        """Derives multipliers for boundary, dot, and wicket likelihood from player stats."""
        modifiers = {
            "boundary_mult": 1.0,
            "dot_mult": 1.0,
            "wicket_mult": 1.0,
            "strike_rate": 130.0,
        }
        if self.player_stats is not None and not self.player_stats.empty:
            if batter_name:
                b_row = self.player_stats[self.player_stats["Player_Name"].str.lower() == batter_name.lower()]
                if not b_row.empty:
                    sr = float(b_row["Strike_Rate"].iloc[0])
                    b_pct = float(b_row.get("Boundary_Percentage", pd.Series([55.0])).iloc[0])
                    modifiers["strike_rate"] = sr
                    modifiers["boundary_mult"] = max(0.6, min(1.6, sr / 130.0))
                    modifiers["dot_mult"] = max(0.6, min(1.4, (100.0 - b_pct) / 45.0))

            if bowler_name:
                bw_row = self.player_stats[self.player_stats["Player_Name"].str.lower() == bowler_name.lower()]
                if not bw_row.empty:
                    econ = float(bw_row.get("Economy", pd.Series([8.0])).iloc[0])
                    sr_bowl = float(bw_row.get("Bowling_Strike_Rate", pd.Series([20.0])).iloc[0])
                    if econ > 0:
                        modifiers["boundary_mult"] *= max(0.7, min(1.4, econ / 8.0))
                    if sr_bowl > 0:
                        modifiers["wicket_mult"] = max(0.6, min(1.6, 20.0 / sr_bowl))

        return modifiers

    def _adjust_distribution(self, phase: str, modifiers: Dict[str, float], rrr: float = 0.0) -> np.ndarray:
        """Adjusts ball outcome probabilities based on phase, player quality, and pressure."""
        base = self.PHASE_BASE_PROBS[phase].copy()
        
        # Apply modifiers
        b_mult = modifiers.get("boundary_mult", 1.0)
        d_mult = modifiers.get("dot_mult", 1.0)
        w_mult = modifiers.get("wicket_mult", 1.0)

        if rrr > 12.0:
            # Desperation batting: higher boundary attempt, higher wicket risk
            b_mult *= 1.2
            w_mult *= 1.3
            d_mult *= 0.8
        elif rrr > 0 and rrr < 6.0:
            # Low risk chasing
            b_mult *= 0.8
            w_mult *= 0.7
            d_mult *= 0.9

        p_0 = base[0] * d_mult
        p_1 = base[1]
        p_2 = base[2]
        p_3 = base[3]
        p_4 = base[4] * b_mult
        p_6 = base[6] * b_mult
        p_w = base["W"] * w_mult

        probs = np.array([p_0, p_1, p_2, p_3, p_4, p_6, p_w], dtype=np.float64)
        total = probs.sum()
        if total > 0:
            probs /= total
        else:
            probs = np.array([0.35, 0.35, 0.08, 0.01, 0.12, 0.05, 0.04])
        return probs

    def simulate(
        self,
        current_score: int,
        current_wickets: int,
        current_over: int,
        current_ball: int = 0,
        target: Optional[int] = None,
        total_overs: int = 20,
        num_simulations: int = 1000,
        batter_name: Optional[str] = None,
        bowler_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs stochastic Monte Carlo simulation across N trajectories."""
        num_simulations = max(100, min(5000, num_simulations))
        start_ball_num = min(total_overs * 6, current_over * 6 + current_ball)
        remaining_balls = (total_overs * 6) - start_ball_num

        if remaining_balls <= 0 or current_wickets >= 10:
            final_scores = np.full(num_simulations, current_score)
            win_count = num_simulations if (target and current_score >= target) else 0
            win_prob = (win_count / num_simulations) * 100 if target else 50.0
            return self._format_results(
                final_scores=final_scores,
                final_wickets=np.full(num_simulations, current_wickets),
                target=target,
                current_score=current_score,
                current_wickets=current_wickets,
                num_simulations=num_simulations,
                win_prob=win_prob,
            )

        modifiers = self._get_player_modifiers(batter_name, bowler_name)
        outcomes = [0, 1, 2, 3, 4, 6, "W"]

        # Precompute distribution per phase
        prob_cache = {}
        for ph in ["powerplay", "middle", "death"]:
            prob_cache[ph] = self._adjust_distribution(ph, modifiers)

        final_scores = []
        final_wickets = []
        wins = 0

        for _ in range(num_simulations):
            score = current_score
            wickets = current_wickets
            
            for b in range(start_ball_num, total_overs * 6):
                if wickets >= 10:
                    break
                if target and score >= target:
                    break

                over_idx = b // 6
                if over_idx < 6:
                    phase = "powerplay"
                elif over_idx >= 15:
                    phase = "death"
                else:
                    phase = "middle"

                # If chasing with dynamic RRR adjustment
                if target and target > score:
                    balls_left = (total_overs * 6) - b
                    rrr = ((target - score) / max(1, balls_left)) * 6.0
                    probs = self._adjust_distribution(phase, modifiers, rrr)
                else:
                    probs = prob_cache[phase]

                # Sample single ball
                res = np.random.choice(outcomes, p=probs)
                if res == "W":
                    wickets += 1
                else:
                    score += int(res)

            final_scores.append(score)
            final_wickets.append(wickets)
            if target and score >= target:
                wins += 1

        final_scores = np.array(final_scores)
        final_wickets = np.array(final_wickets)

        if target:
            win_prob = round((wins / num_simulations) * 100, 2)
        else:
            # For 1st innings, project win prob against benchmark 165
            med = float(np.median(final_scores))
            win_prob = round(max(5.0, min(95.0, 50.0 + (med - 165.0) * 1.2)), 2)

        return self._format_results(
            final_scores=final_scores,
            final_wickets=final_wickets,
            target=target,
            current_score=current_score,
            current_wickets=current_wickets,
            num_simulations=num_simulations,
            win_prob=win_prob,
        )

    def _format_results(
        self,
        final_scores: np.ndarray,
        final_wickets: np.ndarray,
        target: Optional[int],
        current_score: int,
        current_wickets: int,
        num_simulations: int,
        win_prob: float,
    ) -> Dict[str, Any]:
        """Formats the simulation arrays into rich statistical distributions and histogram bins."""
        median_score = float(np.median(final_scores))
        mean_score = float(np.mean(final_scores))
        std_score = float(np.std(final_scores))
        min_score = int(np.min(final_scores))
        max_score = int(np.max(final_scores))

        p10, p25, p50, p75, p90 = [
            float(np.percentile(final_scores, q)) for q in [10, 25, 50, 75, 90]
        ]

        # Build histogram bins (bucketed every 10 runs)
        bin_width = 10
        low_bin = (min_score // bin_width) * bin_width
        high_bin = ((max_score // bin_width) + 1) * bin_width
        bins = np.arange(low_bin, high_bin + bin_width, bin_width)
        
        hist, bin_edges = np.histogram(final_scores, bins=bins)
        distribution = []
        for i in range(len(hist)):
            distribution.append({
                "range": f"{int(bin_edges[i])}-{int(bin_edges[i+1])-1}",
                "min": int(bin_edges[i]),
                "max": int(bin_edges[i+1]),
                "count": int(hist[i]),
                "probability": round(float(hist[i] / num_simulations), 4),
            })

        # Most likely score range
        if distribution:
            top_bin = max(distribution, key=lambda x: x["count"])
            most_likely = top_bin["range"]
        else:
            most_likely = f"{int(median_score)}"

        return {
            "simulations_run": num_simulations,
            "target": target,
            "win_probability_pct": win_prob,
            "median_score": round(median_score, 1),
            "mean_score": round(mean_score, 1),
            "std_score": round(std_score, 2),
            "min_score": min_score,
            "max_score": max_score,
            "percentiles": {
                "p10": round(p10, 1),
                "p25": round(p25, 1),
                "p50": round(p50, 1),
                "p75": round(p75, 1),
                "p90": round(p90, 1),
            },
            "expected_wickets_lost": round(float(np.mean(final_wickets - current_wickets)), 1),
            "expected_wickets_remaining": round(10.0 - float(np.mean(final_wickets)), 1),
            "most_likely_score_range": most_likely,
            "score_distribution": distribution,
        }
