"""
Backend Configuration — Phase 4
Centralizes paths, settings, and CORS origins for the FastAPI backend.
All tuneable values are read from environment variables with safe defaults.
"""

import os
from pathlib import Path

# ── Project Root ─────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Model Paths ──────────────────────────────────────────────────────
MOMENTUM_MODEL_DIR = PROJECT_ROOT / "models" / "momentum"
WIN_PREDICTION_MODEL_DIR = PROJECT_ROOT / "models" / "win_prediction"
EXPLAINABILITY_DIR = PROJECT_ROOT / "models" / "explainability"
RECOMMENDATION_DIR = PROJECT_ROOT / "models" / "recommendation"
SIMULATION_DIR = PROJECT_ROOT / "models" / "simulation"

# ── Data Paths ───────────────────────────────────────────────────────
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
FEATURES_DIR = DATA_DIR / "features"
PLAYER_STATS_PATH = PROCESSED_DIR / "player_stats.csv"
TEAM_STATS_PATH = PROCESSED_DIR / "team_stats.csv"
VENUE_STATS_PATH = PROCESSED_DIR / "venue_stats.csv"

# ── API Settings ─────────────────────────────────────────────────────
API_TITLE = "Cricket Analytics API"
API_VERSION = "1.0.0"
API_DESCRIPTION = (
    "Production-ready REST API for cricket match intelligence. "
    "Exposes win prediction, momentum detection, player recommendations, "
    "explainability, and what-if simulations."
)

# ── CORS — read from env var so production domain requires no code change ──
_cors_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:5000,"
    "http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:5173,"
    "http://127.0.0.1:5000,http://127.0.0.1:8000",
)
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _cors_env.split(",") if o.strip()]

# ── Authentication ────────────────────────────────────────────────────
# Set BACKEND_API_KEY in .env / environment. Requests must send:
#   X-API-Key: <value>
# Set to empty string to disable key checking (development only).
BACKEND_API_KEY: str = os.getenv("BACKEND_API_KEY", "")

# ── Season default ────────────────────────────────────────────────────
DEFAULT_SEASON: str = os.getenv("DEFAULT_SEASON", "2024")

# ── RapidAPI / live settings ──────────────────────────────────────────
API_TIMEOUT_SECONDS: int = int(os.getenv("API_TIMEOUT_SECONDS", "10"))

# ── Momentum labels ─────────────────────────────────────────────────
MOMENTUM_LABELS = {0: "Negative", 1: "Neutral", 2: "Positive"}
