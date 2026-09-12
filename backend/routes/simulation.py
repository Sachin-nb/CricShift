"""Simulation route — POST /api/simulate"""

import logging
from fastapi import APIRouter, HTTPException
from backend.dependencies import model_store
from backend.schemas import (
    SimulationRequest, SimulationResponse,
    MonteCarloRequest, MonteCarloResponse,
)
from backend.live.activity_db import log_simulation

logger = logging.getLogger("backend")
router = APIRouter(tags=["Simulation"])

# Momentum int label → string
_MOM_LABELS = {0: "Negative", 1: "Neutral", 2: "Positive"}


def _normalise_side(side: dict, batting_team: str, bowling_team: str) -> dict:
    """
    Reshape one 'side' dict (original or modified) from the simulation engine
    into the shape the frontend expects:

    Engine produces:
        win_probability_pct   : float   (batting-team win %)
        win_probabilities     : {"Win": float, "Loss": float}
        momentum_class        : int     (0 / 1 / 2)
        momentum_label        : str
        momentum_probabilities: {"Negative": float, "Neutral": float, "Positive": float}

    Frontend reads:
        win_probability       : {batting_team: float, bowling_team: float}
        momentum_class        : str   ("Negative" / "Neutral" / "Positive")
    """
    out = dict(side)

    # ── win_probability keyed by team name ────────────────────────────
    raw_win_prob = side.get("win_probabilities", {})
    batting_pct = side.get("win_probability_pct", float(raw_win_prob.get("Win", 0.5) * 100))
    bowling_pct = 100.0 - batting_pct
    out["win_probability"] = {
        batting_team: round(batting_pct, 2),
        bowling_team: round(bowling_pct, 2),
    }

    # ── momentum_class as string ──────────────────────────────────────
    raw_cls = side.get("momentum_class", 1)
    if isinstance(raw_cls, int):
        out["momentum_class"] = _MOM_LABELS.get(raw_cls, "Neutral")
    # if it's already a string (e.g. "Positive") leave it as-is

    return out


def _normalise_delta(delta: dict, original: dict, modified: dict) -> dict:
    """Add a human-readable win_prob key to delta if the engine didn't."""
    out = dict(delta)
    # engine already includes win_probability_delta; add win_prob alias for frontend
    if "win_probability_delta" in out and "win_prob" not in out:
        out["win_prob"] = out["win_probability_delta"]
    return out


@router.post(
    "/api/simulate",
    response_model=SimulationResponse,
    summary="Run a what-if simulation",
    description="Modifies match state and re-runs Phase 3A/3B models to compare outcomes.",
)
async def simulate(req: SimulationRequest):
    if not model_store.simulation_loaded:
        raise HTTPException(
            503,
            detail=(
                "Simulation engine not loaded. "
                "Check /api/health for details on which models failed to load."
            ),
        )

    try:
        feature_row = model_store.build_feature_row(req.model_dump())
        baseline = feature_row.iloc[0]

        raw = model_store.simulation_engine.simulate(
            original_row=baseline,
            modifications=req.modifications,
            scenario_name=req.scenario_name,
        )

        batting_team = req.batting_team
        bowling_team = req.bowling_team

        original_shaped = _normalise_side(raw["original"], batting_team, bowling_team)
        modified_shaped  = _normalise_side(raw["modified"],  batting_team, bowling_team)
        delta_shaped     = _normalise_delta(raw["delta"],    original_shaped, modified_shaped)

        response = SimulationResponse(
            scenario_name=raw["scenario_name"],
            modifications=raw["modifications"],
            original=original_shaped,
            modified=modified_shaped,
            delta=delta_shaped,
            explanation=raw["explanation"],
        )

        # ── activity log (fire-and-forget) ────────────────────────────
        try:
            log_simulation(req_data=req.model_dump(), result=raw)
        except Exception:
            pass

        return response

    except Exception as e:
        logger.exception("Simulation failed")
        raise HTTPException(500, detail=f"Simulation error: {str(e)}")


@router.post(
    "/api/simulate/monte-carlo",
    response_model=MonteCarloResponse,
    summary="Run stochastic Monte Carlo match simulations",
    description=(
        "Simulates remaining balls across N trajectories (default 1000) using "
        "phase distributions and player modifier statistics to produce full probability curves."
    ),
)
async def simulate_monte_carlo(req: MonteCarloRequest):
    if not model_store.monte_carlo_loaded or model_store.monte_carlo_simulator is None:
        raise HTTPException(
            503,
            detail="Monte Carlo simulator not loaded. Check /api/health.",
        )

    try:
        results = model_store.monte_carlo_simulator.simulate(
            current_score=req.current_score,
            current_wickets=req.current_wickets,
            current_over=req.current_over,
            current_ball=req.current_ball,
            target=req.target,
            total_overs=req.total_overs,
            num_simulations=req.num_simulations,
            batter_name=req.batter_name,
            bowler_name=req.bowler_name,
        )
        return MonteCarloResponse(**results)
    except Exception as e:
        logger.exception("Monte Carlo simulation failed")
        raise HTTPException(500, detail=f"Monte Carlo simulation error: {str(e)}")

