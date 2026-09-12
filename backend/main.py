"""
Cricket Analytics API — FastAPI Application (Phase 4)
=====================================================
Production-ready REST API layer over existing ML models and engines.

Start with:
    uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
"""

import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Ensure project root is on sys.path ───────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import (
    API_TITLE, API_VERSION, API_DESCRIPTION, ALLOWED_ORIGINS, BACKEND_API_KEY,
)
from backend.dependencies import model_store

# ── Routes ───────────────────────────────────────────────────────────
from backend.routes import health, prediction, momentum, recommendation
from backend.routes import explainability, simulation, analytics, live_routes, historical
from backend.routes import admin as admin_routes
from backend.routes import auth as auth_routes

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("backend")


# ═════════════════════════════════════════════════════════════════════
# LIFESPAN — Load models and initialise DB at startup
# ═════════════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("  Cricket Analytics API — Starting")
    logger.info("=" * 60)

    # Initialise SQLite DB (moved from module-level in db.py)
    try:
        from backend.live.db import init_db
        init_db()
        logger.info("  ✓ SQLite database ready")
    except Exception as e:
        logger.warning(f"  ✗ SQLite init skipped: {e}")

    # Initialise activity DB for admin panel
    try:
        from backend.live.activity_db import init_activity_db
        init_activity_db()
        logger.info("  ✓ Activity DB ready")
    except Exception as e:
        logger.warning(f"  ✗ Activity DB init skipped: {e}")

    t0 = time.time()
    status = model_store.load_all()
    elapsed = round(time.time() - t0, 2)
    logger.info(f"  Model loading completed in {elapsed}s")
    for name, ok in status.items():
        icon = "✓" if ok else "✗"
        logger.info(f"    {icon} {name}")

    if BACKEND_API_KEY:
        logger.info("  ✓ API key authentication enabled")
    else:
        logger.warning("  ⚠ BACKEND_API_KEY not set — authentication disabled (development mode)")

    logger.info("=" * 60)
    yield  # Application runs
    logger.info("Cricket Analytics API — Shutting down")


# ═════════════════════════════════════════════════════════════════════
# APP
# ═════════════════════════════════════════════════════════════════════
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Register routes ──────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(prediction.router)
app.include_router(momentum.router)
app.include_router(recommendation.router)
app.include_router(explainability.router)
app.include_router(simulation.router)
app.include_router(analytics.router)
app.include_router(live_routes.router)
app.include_router(historical.router)
app.include_router(admin_routes.router)
app.include_router(auth_routes.router)


# ═════════════════════════════════════════════════════════════════════
# AUTHENTICATION MIDDLEWARE
# ─────────────────────────────────────────────────────────────────────
# If BACKEND_API_KEY is set, every non-docs request must include:
#   X-API-Key: <value>
# Exempted paths: /, /docs, /redoc, /openapi.json, /api/health
# ═════════════════════════════════════════════════════════════════════
_AUTH_EXEMPT = {
    "/", "/docs", "/redoc", "/openapi.json", "/api/health", "/api/admin/stats",
    # Auth endpoints are public — they authenticate the user themselves
    "/api/auth/register", "/api/auth/login",
    "/api/auth/register/send-otp", "/api/auth/register/verify-otp",
    "/api/auth/send-otp", "/api/auth/verify-otp", "/api/auth/reset-password",
    "/api/auth/google", "/api/auth/config",
}


@app.middleware("http")
async def api_key_auth(request: Request, call_next):
    if BACKEND_API_KEY and request.url.path not in _AUTH_EXEMPT:
        key = request.headers.get("X-API-Key", "")
        if key != BACKEND_API_KEY:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "detail": "Invalid or missing X-API-Key header"},
            )
    return await call_next(request)


# ── Request logging middleware ───────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    t0 = time.time()
    response = await call_next(request)
    elapsed = round((time.time() - t0) * 1000, 1)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({elapsed}ms)")
    return response


# ── Global exception handler ─────────────────────────────────────────
# Logs full detail server-side but returns a generic message to the client
# to prevent leaking internal paths, column names, or stack frames.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc!r}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again or contact support.",
            "status_code": 500,
        },
    )


# ── Root redirect ────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Cricket Analytics API", "docs": "/docs"}


@app.websocket("/ws/live/{match_id}")
async def ws_live_redirect(websocket: WebSocket, match_id: str):
    from backend.routes.live_routes import live_websocket_endpoint
    await live_websocket_endpoint(websocket, match_id)
