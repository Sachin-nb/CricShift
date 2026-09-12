"""
activity_db.py — Admin activity tracking database.

Stores every significant user action (live match fetch, prediction, simulation,
historical upload) into a separate SQLite file: data/admin_activity.db

Tables
------
live_matches
    id, match_id, team_a, team_b, series, venue, match_format, status,
    first_seen_at, last_seen_at, fetch_count

predictions
    id, type (win|momentum|match), batting_team, bowling_team, venue,
    innings, current_over, current_score, current_wickets, target,
    predicted_winner, win_prob_batting, momentum_class, confidence,
    created_at

simulations
    id, scenario_name, batting_team, bowling_team, venue, innings,
    current_over, current_score, current_wickets, target,
    modifications_json, original_win_prob, modified_win_prob,
    original_momentum, modified_momentum, delta_json, explanation,
    created_at

historical_analyses
    id, analysis_id, filename, match_id, batting_team, bowling_team,
    venue, timeline_length, turning_points_count, file_size_kb,
    created_at
"""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
ACTIVITY_DB_PATH = DATA_DIR / "admin_activity.db"

# ─────────────────────────────────────────────────────────────────────────────
# Connection helper
# ─────────────────────────────────────────────────────────────────────────────

@contextmanager
def _conn():
    """WAL-mode SQLite connection context manager."""
    con = sqlite3.connect(ACTIVITY_DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


# ─────────────────────────────────────────────────────────────────────────────
# Schema init
# ─────────────────────────────────────────────────────────────────────────────

def init_activity_db() -> None:
    """Create tables if they don't exist. Safe to call multiple times."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with _conn() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS live_matches (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id        TEXT    NOT NULL,
            team_a          TEXT    NOT NULL DEFAULT '',
            team_b          TEXT    NOT NULL DEFAULT '',
            series          TEXT    NOT NULL DEFAULT '',
            venue           TEXT    NOT NULL DEFAULT '',
            match_format    TEXT    NOT NULL DEFAULT 'T20',
            status          TEXT    NOT NULL DEFAULT '',
            first_seen_at   TEXT    NOT NULL,
            last_seen_at    TEXT    NOT NULL,
            fetch_count     INTEGER NOT NULL DEFAULT 1,
            UNIQUE(match_id)
        );

        CREATE TABLE IF NOT EXISTS predictions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            type            TEXT    NOT NULL DEFAULT 'win',
            batting_team    TEXT    NOT NULL DEFAULT '',
            bowling_team    TEXT    NOT NULL DEFAULT '',
            venue           TEXT    NOT NULL DEFAULT '',
            innings         INTEGER NOT NULL DEFAULT 1,
            current_over    INTEGER NOT NULL DEFAULT 0,
            current_score   INTEGER NOT NULL DEFAULT 0,
            current_wickets INTEGER NOT NULL DEFAULT 0,
            target          INTEGER NOT NULL DEFAULT 0,
            predicted_winner TEXT   NOT NULL DEFAULT '',
            win_prob_batting REAL   NOT NULL DEFAULT 50.0,
            momentum_class  TEXT    NOT NULL DEFAULT '',
            confidence      REAL    NOT NULL DEFAULT 0.0,
            created_at      TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS simulations (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario_name       TEXT    NOT NULL DEFAULT '',
            batting_team        TEXT    NOT NULL DEFAULT '',
            bowling_team        TEXT    NOT NULL DEFAULT '',
            venue               TEXT    NOT NULL DEFAULT '',
            innings             INTEGER NOT NULL DEFAULT 1,
            current_over        INTEGER NOT NULL DEFAULT 0,
            current_score       INTEGER NOT NULL DEFAULT 0,
            current_wickets     INTEGER NOT NULL DEFAULT 0,
            target              INTEGER NOT NULL DEFAULT 0,
            modifications_json  TEXT    NOT NULL DEFAULT '{}',
            original_win_prob   REAL    NOT NULL DEFAULT 50.0,
            modified_win_prob   REAL    NOT NULL DEFAULT 50.0,
            original_momentum   TEXT    NOT NULL DEFAULT '',
            modified_momentum   TEXT    NOT NULL DEFAULT '',
            delta_json          TEXT    NOT NULL DEFAULT '{}',
            explanation         TEXT    NOT NULL DEFAULT '',
            created_at          TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS historical_analyses (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id          TEXT    NOT NULL UNIQUE,
            filename             TEXT    NOT NULL DEFAULT '',
            match_id             TEXT    NOT NULL DEFAULT '',
            batting_team         TEXT    NOT NULL DEFAULT '',
            bowling_team         TEXT    NOT NULL DEFAULT '',
            venue                TEXT    NOT NULL DEFAULT '',
            timeline_length      INTEGER NOT NULL DEFAULT 0,
            turning_points_count INTEGER NOT NULL DEFAULT 0,
            file_size_kb         REAL    NOT NULL DEFAULT 0.0,
            result_json          TEXT    NOT NULL DEFAULT '{}',
            created_at           TEXT    NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_lm_match_id  ON live_matches (match_id);
        CREATE INDEX IF NOT EXISTS idx_pred_created  ON predictions (created_at);
        CREATE INDEX IF NOT EXISTS idx_sim_created   ON simulations (created_at);
        CREATE INDEX IF NOT EXISTS idx_hist_created  ON historical_analyses (created_at);
        """)
    logger.info(f"Activity DB ready at {ACTIVITY_DB_PATH}")


# ─────────────────────────────────────────────────────────────────────────────
# Write helpers
# ─────────────────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_live_match(match: Dict[str, Any]) -> None:
    """Upsert a live match record. Increments fetch_count on repeat visits."""
    match_id = str(match.get("match_id", ""))
    if not match_id:
        return
    now = _now()
    try:
        with _conn() as con:
            existing = con.execute(
                "SELECT id FROM live_matches WHERE match_id = ?", (match_id,)
            ).fetchone()
            if existing:
                con.execute(
                    """UPDATE live_matches
                       SET last_seen_at = ?, fetch_count = fetch_count + 1,
                           status = ?, team_a = ?, team_b = ?, series = ?,
                           venue = ?, match_format = ?
                       WHERE match_id = ?""",
                    (
                        now,
                        str(match.get("status", "")),
                        str(match.get("team_a", "")),
                        str(match.get("team_b", "")),
                        str(match.get("series", "")),
                        str(match.get("venue", "")),
                        str(match.get("match_format", "T20")),
                        match_id,
                    ),
                )
            else:
                con.execute(
                    """INSERT INTO live_matches
                       (match_id, team_a, team_b, series, venue, match_format,
                        status, first_seen_at, last_seen_at, fetch_count)
                       VALUES (?,?,?,?,?,?,?,?,?,1)""",
                    (
                        match_id,
                        str(match.get("team_a", "")),
                        str(match.get("team_b", "")),
                        str(match.get("series", "")),
                        str(match.get("venue", "")),
                        str(match.get("match_format", "T20")),
                        str(match.get("status", "")),
                        now,
                        now,
                    ),
                )
    except Exception as e:
        logger.warning(f"log_live_match failed: {e}")


def log_prediction(
    pred_type: str,
    req_data: Dict[str, Any],
    result: Dict[str, Any],
) -> None:
    """Record a win/momentum/match prediction call."""
    try:
        win_prob = result.get("win_probability", {})
        batting  = req_data.get("batting_team", "")
        win_pct  = float(win_prob.get(batting, 50.0)) if isinstance(win_prob, dict) else 50.0
        with _conn() as con:
            con.execute(
                """INSERT INTO predictions
                   (type, batting_team, bowling_team, venue, innings,
                    current_over, current_score, current_wickets, target,
                    predicted_winner, win_prob_batting, momentum_class,
                    confidence, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    pred_type,
                    batting,
                    req_data.get("bowling_team", ""),
                    req_data.get("venue", ""),
                    int(req_data.get("innings", 1)),
                    int(req_data.get("current_over", 0)),
                    int(req_data.get("current_score", 0)),
                    int(req_data.get("current_wickets", 0)),
                    int(req_data.get("target", 0)),
                    str(result.get("predicted_winner", "")),
                    win_pct,
                    str(result.get("momentum_class", "")),
                    float(result.get("confidence", 0.0)),
                    _now(),
                ),
            )
    except Exception as e:
        logger.warning(f"log_prediction failed: {e}")


def log_simulation(
    req_data: Dict[str, Any],
    result: Dict[str, Any],
) -> None:
    """Record a what-if simulation call."""
    try:
        orig = result.get("original", {})
        mod  = result.get("modified", {})
        delta = result.get("delta", {})

        def _win(d: Dict) -> float:
            wp = d.get("win_probability", {})
            if isinstance(wp, dict):
                batting = req_data.get("batting_team", "")
                return float(wp.get(batting, next(iter(wp.values()), 50.0)))
            return 50.0

        with _conn() as con:
            con.execute(
                """INSERT INTO simulations
                   (scenario_name, batting_team, bowling_team, venue, innings,
                    current_over, current_score, current_wickets, target,
                    modifications_json, original_win_prob, modified_win_prob,
                    original_momentum, modified_momentum, delta_json,
                    explanation, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(req_data.get("scenario_name", "Custom Scenario")),
                    req_data.get("batting_team", ""),
                    req_data.get("bowling_team", ""),
                    req_data.get("venue", ""),
                    int(req_data.get("innings", 1)),
                    int(req_data.get("current_over", 0)),
                    int(req_data.get("current_score", 0)),
                    int(req_data.get("current_wickets", 0)),
                    int(req_data.get("target", 0)),
                    json.dumps(req_data.get("modifications", {})),
                    _win(orig),
                    _win(mod),
                    str(orig.get("momentum_class", "")),
                    str(mod.get("momentum_class", "")),
                    json.dumps(delta),
                    str(result.get("explanation", "")),
                    _now(),
                ),
            )
    except Exception as e:
        logger.warning(f"log_simulation failed: {e}")


def log_historical_analysis(
    analysis_id: str,
    filename: str,
    file_size_kb: float,
    match_info: Dict[str, Any],
    timeline_length: int,
    turning_points_count: int,
    full_result: Dict[str, Any],
) -> None:
    """Record a historical CSV upload + analysis result."""
    try:
        with _conn() as con:
            con.execute(
                """INSERT OR REPLACE INTO historical_analyses
                   (analysis_id, filename, match_id, batting_team, bowling_team,
                    venue, timeline_length, turning_points_count,
                    file_size_kb, result_json, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    analysis_id,
                    filename,
                    str(match_info.get("match_id", "")),
                    str(match_info.get("batting_team", "")),
                    str(match_info.get("bowling_team", "")),
                    str(match_info.get("venue", "")),
                    timeline_length,
                    turning_points_count,
                    round(file_size_kb, 2),
                    json.dumps(full_result),
                    _now(),
                ),
            )
    except Exception as e:
        logger.warning(f"log_historical_analysis failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Read helpers  (used by admin routes)
# ─────────────────────────────────────────────────────────────────────────────

def get_dashboard_stats() -> Dict[str, Any]:
    """Aggregate KPI counts for the admin dashboard."""
    try:
        with _conn() as con:
            stats = {
                "total_live_matches":      con.execute("SELECT COUNT(*) FROM live_matches").fetchone()[0],
                "total_predictions":       con.execute("SELECT COUNT(*) FROM predictions").fetchone()[0],
                "total_simulations":       con.execute("SELECT COUNT(*) FROM simulations").fetchone()[0],
                "total_historical":        con.execute("SELECT COUNT(*) FROM historical_analyses").fetchone()[0],
                "live_matches_today":      con.execute(
                    "SELECT COUNT(*) FROM live_matches WHERE date(last_seen_at) = date('now')"
                ).fetchone()[0],
                "predictions_today":       con.execute(
                    "SELECT COUNT(*) FROM predictions WHERE date(created_at) = date('now')"
                ).fetchone()[0],
                "simulations_today":       con.execute(
                    "SELECT COUNT(*) FROM simulations WHERE date(created_at) = date('now')"
                ).fetchone()[0],
                "historical_today":        con.execute(
                    "SELECT COUNT(*) FROM historical_analyses WHERE date(created_at) = date('now')"
                ).fetchone()[0],
            }
        return stats
    except Exception as e:
        logger.warning(f"get_dashboard_stats failed: {e}")
        return {}


def get_live_matches(limit: int = 100, offset: int = 0) -> List[Dict]:
    try:
        with _conn() as con:
            rows = con.execute(
                """SELECT * FROM live_matches
                   ORDER BY last_seen_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"get_live_matches failed: {e}")
        return []


def get_predictions(limit: int = 100, offset: int = 0) -> List[Dict]:
    try:
        with _conn() as con:
            rows = con.execute(
                """SELECT * FROM predictions
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"get_predictions failed: {e}")
        return []


def get_simulations(limit: int = 100, offset: int = 0) -> List[Dict]:
    try:
        with _conn() as con:
            rows = con.execute(
                """SELECT * FROM simulations
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"get_simulations failed: {e}")
        return []


def get_historical_analyses(limit: int = 100, offset: int = 0) -> List[Dict]:
    try:
        with _conn() as con:
            rows = con.execute(
                """SELECT id, analysis_id, filename, match_id, batting_team,
                          bowling_team, venue, timeline_length,
                          turning_points_count, file_size_kb, created_at
                   FROM historical_analyses
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"get_historical_analyses failed: {e}")
        return []


def get_historical_analysis_by_id(analysis_id: str) -> Optional[Dict]:
    """Return the full stored result JSON for a single analysis (used by analysis page re-fetch)."""
    try:
        with _conn() as con:
            row = con.execute(
                "SELECT result_json FROM historical_analyses WHERE analysis_id = ?",
                (analysis_id,),
            ).fetchone()
        if row:
            return json.loads(row["result_json"])
        return None
    except Exception as e:
        logger.warning(f"get_historical_analysis_by_id failed: {e}")
        return None
