import sqlite3
import pandas as pd
from pathlib import Path
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Absolute paths based on project structure
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "cricket_historical.db"

CSV_PATHS = {
    "players": DATA_DIR / "processed" / "player_stats.csv",
    "teams": DATA_DIR / "processed" / "team_stats.csv",
    "venues": DATA_DIR / "processed" / "venue_stats.csv",
    "matchups": DATA_DIR / "processed" / "matchups.csv",
}


@contextmanager
def get_connection():
    """
    Context-manager that opens a WAL-mode SQLite connection and guarantees
    it is closed even if an exception is raised.

    Usage:
        with get_connection() as conn:
            row = conn.execute("SELECT ...").fetchone()
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # WAL mode allows concurrent readers alongside a writer — crucial for
    # async FastAPI where multiple coroutines may query simultaneously.
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """
    Loads CSV files into SQLite if tables don't exist yet.
    Called once at application startup from main.py lifespan, NOT at import time.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    try:
        for table_name, csv_path in CSV_PATHS.items():
            if not csv_path.exists():
                logger.warning(f"Cannot find {csv_path}. Table '{table_name}' skipped.")
                continue

            # Check if table already exists
            cursor = conn.cursor()
            cursor.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            exists = cursor.fetchone()[0] > 0
            if exists:
                continue

            logger.info(f"Loading {csv_path.name} into table '{table_name}'...")
            df = pd.read_csv(csv_path)
            df.to_sql(table_name, conn, if_exists="replace", index=False)

        # Indexes for fast lookup
        cursor = conn.cursor()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_player_name ON players (Player_Name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_team_name ON teams (Team);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_venue_name ON venues (Venue);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matchup_batter ON matchups (Batter);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matchup_bowler ON matchups (Bowler);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_matchup_pair ON matchups (Batter, Bowler);")
        conn.commit()
        logger.info("Database initialization complete.")
    finally:
        conn.close()


def get_player_stats(player_name: str) -> dict:
    """Fetches historical player stats by exact name match."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM players WHERE Player_Name = ?", (player_name,)
        ).fetchone()
    return dict(row) if row else {}


def get_team_stats(team_name: str) -> dict:
    """Fetches historical team stats by exact name match."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM teams WHERE Team = ?", (team_name,)
        ).fetchone()
    return dict(row) if row else {}


def get_venue_stats(venue_name: str) -> dict:
    """Fetches historical venue stats by exact name match."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM venues WHERE Venue = ?", (venue_name,)
        ).fetchone()
    return dict(row) if row else {}


def get_all_player_names() -> list:
    """Returns a list of all player names for fuzzy matching."""
    with get_connection() as conn:
        rows = conn.execute("SELECT Player_Name FROM players").fetchall()
    return [row["Player_Name"] for row in rows]


def get_all_team_names() -> list:
    """Returns a list of all team names for fuzzy matching."""
    with get_connection() as conn:
        rows = conn.execute("SELECT Team FROM teams").fetchall()
    return [row["Team"] for row in rows]


def get_all_venue_names() -> list:
    """Returns a list of all venue names for fuzzy matching."""
    with get_connection() as conn:
        rows = conn.execute("SELECT Venue FROM venues").fetchall()
    return [row["Venue"] for row in rows]


def get_matchup(batter_name: str, bowler_name: str) -> dict:
    """Fetches head-to-head stats between a specific batter and bowler."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM matchups 
            WHERE lower(Batter) = lower(?) AND lower(Bowler) = lower(?)
            """,
            (batter_name.strip(), bowler_name.strip()),
        ).fetchone()
    return dict(row) if row else {}


def get_batter_matchups(batter_name: str, min_balls: int = 0, limit: int = 50) -> list:
    """Returns all bowler matchups for a given batter, sorted by balls faced desc."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM matchups 
            WHERE lower(Batter) = lower(?) AND Balls_Faced >= ?
            ORDER BY Balls_Faced DESC LIMIT ?
            """,
            (batter_name.strip(), min_balls, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_bowler_matchups(bowler_name: str, min_balls: int = 0, limit: int = 50) -> list:
    """Returns all batter matchups for a given bowler, sorted by dismissals desc, then balls faced."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM matchups 
            WHERE lower(Bowler) = lower(?) AND Balls_Faced >= ?
            ORDER BY Dismissals DESC, Balls_Faced DESC LIMIT ?
            """,
            (bowler_name.strip(), min_balls, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_matchup_matrix(batters: list, bowlers: list) -> list:
    """Returns 2D pairwise matchup grid data for a list of batters and bowlers."""
    if not batters or not bowlers:
        return []
    placeholders_bat = ",".join(["?"] * len(batters))
    placeholders_bowl = ",".join(["?"] * len(bowlers))
    bat_lower = [b.lower().strip() for b in batters]
    bowl_lower = [b.lower().strip() for b in bowlers]

    query = f"""
        SELECT * FROM matchups
        WHERE lower(Batter) IN ({placeholders_bat})
          AND lower(Bowler) IN ({placeholders_bowl})
    """
    with get_connection() as conn:
        rows = conn.execute(query, bat_lower + bowl_lower).fetchall()
    return [dict(r) for r in rows]


# NOTE: init_db() is intentionally NOT called here at module import time.
# It is called once during FastAPI lifespan startup in backend/main.py.
