"""Health route — GET /api/health"""

import sys
from fastapi import APIRouter
from backend.dependencies import model_store

router = APIRouter(tags=["Health"])


@router.get(
    "/api/health",
    summary="Service health check",
    description="Returns service status, model-load state, and any startup error messages.",
)
async def health():
    errors = getattr(model_store, "load_errors", {})

    return {
        "status": "ok",
        "service": "cricket-analytics-api",
        "python_version": sys.version,
        "models_loaded": model_store.all_loaded,
        "model_status": {
            "momentum":       model_store.momentum_loaded,
            "win_prediction": model_store.win_loaded,
            "recommendation": model_store.recommendation_loaded,
            "simulation":     model_store.simulation_loaded,
            "reference_data": model_store.data_loaded,
        },
        # Surfaces the exact exception message for any failed component
        "load_errors": errors,
    }
