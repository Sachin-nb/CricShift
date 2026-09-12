"""
Data Loader Module
==================
Responsible for reading, validating, and normalizing ball-by-ball
cricket match data from CSV files. Provides a clean DataFrame that
downstream modules can consume.

Supports multiple CSV formats:
  - Custom format (our generated data)
  - Cricsheet format (ball_by_ball CSV downloads)
  - Kaggle IPL datasets
  - ESPNCricinfo-style exports

The loader auto-detects column names and maps them to our internal schema.
"""

import pandas as pd
import numpy as np
import os

# Internal required column names (after mapping)
REQUIRED_COLUMNS = [
    "innings", "over", "ball", "batting_team", "bowling_team",
    "batsman", "bowler", "runs_off_bat", "extras", "total_runs",
    "is_wicket"
]

# Column name mapping: maps common external names → our internal names
# Each internal name maps to a list of possible source column names,
# checked in priority order (first match wins).
COLUMN_ALIASES = {
    "innings":          ["innings", "inning", "innings_number", "inning_number"],
    "over":             ["over", "overs", "over_number", "over_num"],
    "ball":             ["ball", "ball_number", "ball_num", "delivery", "ball_in_over"],
    "batting_team":     ["batting_team", "bat_team", "team_batting", "team1",
                         "batting_side", "BattingTeam"],
    "bowling_team":     ["bowling_team", "bowl_team", "team_bowling", "team2",
                         "bowling_side", "BowlingTeam"],
    "batsman":          ["batsman", "batter", "striker", "bat_name",
                         "batsman_name", "batter_name", "StrikerName"],
    "bowler":           ["bowler", "bowler_name", "bowl_name", "BowlerName"],
    "runs_off_bat":     ["runs_off_bat", "batsman_runs", "batter_runs",
                         "runs_scored", "batsman_run", "bat_runs", "runs"],
    "extras":           ["extras", "extra_runs", "extra", "extras_run",
                         "wide_runs", "noball_runs"],
    "total_runs":       ["total_runs", "total", "total_run", "runs_total",
                         "run_total"],
    "is_wicket":        ["is_wicket", "wicket", "player_out", "is_wkt",
                         "wicket_fallen"],
    "dismissal_kind":   ["dismissal_kind", "dismissal_type", "kind",
                         "wicket_type", "out_type", "how_out"],
    "player_dismissed": ["player_dismissed", "dismissed_player", "player_out",
                         "out_player", "who_out"],
    "match_id":         ["match_id", "id", "match_no", "match_number",
                         "game_id"],
}


class DataLoader:
    """Load and validate ball-by-ball cricket match data."""

    def __init__(self, filepath: str):
        """
        Initialize DataLoader with path to CSV file.

        Args:
            filepath: Absolute or relative path to the CSV dataset.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If required columns are missing.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Dataset not found: {filepath}")
        self.filepath = filepath
        self._raw_df = None
        self._processed_df = None
        self._column_map = {}  # tracks which source col mapped to which target

    def load(self) -> pd.DataFrame:
        """
        Read the CSV, auto-map columns, validate, and clean.

        Returns:
            Cleaned DataFrame with standardized column types.
        """
        self._raw_df = pd.read_csv(self.filepath)

        # Strip whitespace from column names
        self._raw_df.columns = [c.strip() for c in self._raw_df.columns]

        # Auto-map columns
        self._auto_map_columns()

        # Filter to single match if dataset contains multiple matches
        self._filter_single_match()

        self._validate_columns()
        self._clean_data()
        self._add_computed_columns()
        return self._processed_df.copy()

    def _auto_map_columns(self):
        """
        Auto-detect and rename columns to match our internal schema.
        Uses the COLUMN_ALIASES mapping to find the best match.
        """
        df = self._raw_df
        existing_cols = [c.lower() for c in df.columns]
        rename_map = {}

        for target_name, aliases in COLUMN_ALIASES.items():
            # Skip if the target name already exists in the dataframe
            if target_name in df.columns:
                self._column_map[target_name] = target_name
                continue

            # Search aliases (case-insensitive)
            found = False
            for alias in aliases:
                # Case-insensitive match
                for original_col in df.columns:
                    if original_col.lower() == alias.lower() and original_col not in rename_map:
                        rename_map[original_col] = target_name
                        self._column_map[target_name] = original_col
                        found = True
                        break
                if found:
                    break

        if rename_map:
            self._raw_df = df.rename(columns=rename_map)

    def _filter_single_match(self):
        """
        If the dataset contains multiple matches, keep only the first one.
        This handles large Kaggle-style datasets with many matches.
        """
        df = self._raw_df
        if "match_id" in df.columns:
            match_ids = df["match_id"].unique()
            if len(match_ids) > 1:
                # Keep the first match
                first_match = match_ids[0]
                self._raw_df = df[df["match_id"] == first_match].copy()
                print(f"  ℹ Dataset contains {len(match_ids)} matches. "
                      f"Using first match (ID: {first_match}).")

    def _validate_columns(self):
        """
        Ensure all required columns are present.
        Attempts to derive missing columns before raising errors.
        """
        df = self._raw_df

        # Try to derive 'total_runs' if missing
        if "total_runs" not in df.columns:
            if "runs_off_bat" in df.columns and "extras" in df.columns:
                df["total_runs"] = (
                    pd.to_numeric(df["runs_off_bat"], errors="coerce").fillna(0) +
                    pd.to_numeric(df["extras"], errors="coerce").fillna(0)
                ).astype(int)
                self._raw_df = df
            elif "runs_off_bat" in df.columns:
                df["total_runs"] = pd.to_numeric(
                    df["runs_off_bat"], errors="coerce"
                ).fillna(0).astype(int)
                self._raw_df = df

        # Try to derive 'is_wicket' from 'dismissal_kind' or 'player_dismissed'
        if "is_wicket" not in df.columns:
            if "dismissal_kind" in df.columns:
                df["is_wicket"] = (
                    df["dismissal_kind"].notna() &
                    (df["dismissal_kind"].astype(str).str.strip() != "") &
                    (df["dismissal_kind"].astype(str).str.lower() != "nan")
                ).astype(int)
                self._raw_df = df
            elif "player_dismissed" in df.columns:
                df["is_wicket"] = (
                    df["player_dismissed"].notna() &
                    (df["player_dismissed"].astype(str).str.strip() != "") &
                    (df["player_dismissed"].astype(str).str.lower() != "nan")
                ).astype(int)
                self._raw_df = df

        # Try to derive 'extras' if missing
        if "extras" not in df.columns:
            df["extras"] = 0
            self._raw_df = df

        # Try to derive 'ball' from over if stored as decimal (e.g., 2.3)
        if "ball" not in df.columns and "over" in df.columns:
            over_vals = pd.to_numeric(df["over"], errors="coerce").fillna(0)
            if (over_vals % 1 != 0).any():
                # Over is stored as decimal like 2.3 → over=2, ball=3
                df["ball"] = ((over_vals % 1) * 10).round().astype(int)
                df["over"] = over_vals.astype(int)
                self._raw_df = df

        # Final check for required columns
        missing = [c for c in REQUIRED_COLUMNS if c not in self._raw_df.columns]
        if missing:
            available = list(self._raw_df.columns)
            raise ValueError(
                f"Missing required columns: {missing}.\n"
                f"Your CSV has these columns: {available}.\n"
                f"Expected columns: {REQUIRED_COLUMNS}.\n"
                f"Tip: Rename your columns to match, or check the README for "
                f"the expected CSV format."
            )

    def _clean_data(self):
        """Normalize data types, fill missing values, sort by delivery order."""
        df = self._raw_df.copy()

        # Ensure numeric types
        for col in ["over", "ball", "runs_off_bat", "extras", "total_runs", "is_wicket"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

        # Ensure innings is integer
        df["innings"] = pd.to_numeric(df["innings"], errors="coerce").fillna(1).astype(int)

        # Fill optional string columns
        for col in ["dismissal_kind", "player_dismissed"]:
            if col in df.columns:
                df[col] = df[col].fillna("")
            else:
                df[col] = ""

        if "match_id" not in df.columns:
            df["match_id"] = 1

        # Sort by innings, over, ball
        df = df.sort_values(["innings", "over", "ball"]).reset_index(drop=True)

        self._processed_df = df

    def _add_computed_columns(self):
        """Add derived columns useful for downstream processing."""
        df = self._processed_df

        # Global ball number within each innings (1-indexed)
        df["ball_number"] = df.groupby("innings").cumcount() + 1

        # Over number as float (e.g., 3.4 = over 3, ball 4)
        df["over_exact"] = df["over"] + df["ball"] / 10.0

        # Cumulative runs per innings
        df["cumulative_runs"] = df.groupby("innings")["total_runs"].cumsum()

        # Cumulative wickets per innings
        df["cumulative_wickets"] = df.groupby("innings")["is_wicket"].cumsum()

        # Is boundary (4 or 6 off the bat)
        df["is_boundary"] = df["runs_off_bat"].isin([4, 6]).astype(int)

        # Is dot ball (0 runs off bat and 0 extras)
        df["is_dot"] = ((df["runs_off_bat"] == 0) & (df["extras"] == 0)).astype(int)

        self._processed_df = df

    def get_innings_data(self, innings: int) -> pd.DataFrame:
        """
        Get data for a specific innings.

        Args:
            innings: Innings number (1 or 2).

        Returns:
            DataFrame filtered for the requested innings.
        """
        if self._processed_df is None:
            self.load()
        return self._processed_df[self._processed_df["innings"] == innings].copy()

    def get_teams(self) -> dict:
        """
        Extract team names from the dataset.

        Returns:
            Dictionary with 'team1' and 'team2' keys.
        """
        if self._processed_df is None:
            self.load()

        # Get teams: first batting team in innings 1 is team1
        inn1 = self._processed_df[self._processed_df["innings"] == 1]
        inn2 = self._processed_df[self._processed_df["innings"] == 2]

        if len(inn1) > 0:
            team1 = inn1["batting_team"].iloc[0]
        else:
            teams = self._processed_df["batting_team"].unique().tolist()
            team1 = teams[0] if teams else "Team A"

        if len(inn2) > 0:
            team2 = inn2["batting_team"].iloc[0]
        else:
            # Try bowling team from innings 1
            if len(inn1) > 0:
                team2 = inn1["bowling_team"].iloc[0]
            else:
                teams = self._processed_df["batting_team"].unique().tolist()
                team2 = teams[1] if len(teams) > 1 else "Team B"

        return {"team1": str(team1), "team2": str(team2)}

    def get_match_summary(self) -> dict:
        """
        Get a high-level summary of the match.

        Returns:
            Dictionary with match metadata.
        """
        if self._processed_df is None:
            self.load()
        df = self._processed_df
        teams = self.get_teams()

        innings1 = df[df["innings"] == 1]
        innings2 = df[df["innings"] == 2]

        return {
            "teams": teams,
            "innings1_total": int(innings1["total_runs"].sum()) if len(innings1) > 0 else 0,
            "innings1_wickets": int(innings1["is_wicket"].sum()) if len(innings1) > 0 else 0,
            "innings1_overs": f"{innings1['over'].iloc[-1]}.{innings1['ball'].iloc[-1]}" if len(innings1) > 0 else "0.0",
            "innings2_total": int(innings2["total_runs"].sum()) if len(innings2) > 0 else 0,
            "innings2_wickets": int(innings2["is_wicket"].sum()) if len(innings2) > 0 else 0,
            "innings2_overs": f"{innings2['over'].iloc[-1]}.{innings2['ball'].iloc[-1]}" if len(innings2) > 0 else "0.0",
            "total_balls": len(df),
        }
