import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
import time

from generate_player_stats import PlayerStatsGenerator
from generate_venue_stats import VenueStatsGenerator
from generate_team_stats import TeamStatsGenerator

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def validate_dataframe(df: pd.DataFrame, df_name: str, id_col: str) -> dict:
    report = {
        "Name": df_name,
        "Rows": len(df),
        "Missing_Values": int(df.isna().sum().sum()),
        "Duplicates": int(df.duplicated(subset=[id_col]).sum()),
        "Negative_Values": 0,
        "Inf_Values": 0
    }
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        negatives = (df[col] < 0).sum()
        infs = np.isinf(df[col]).sum()
        report["Negative_Values"] += int(negatives)
        report["Inf_Values"] += int(infs)
        
    return report

def main():
    start_time = time.time()
    PROCESSED_DIR = Path(r"data\processed")
    
    logging.info("Loading matches and ball_by_ball datasets...")
    matches_df = pd.read_csv(PROCESSED_DIR / "matches.csv")
    bbb_df = pd.read_csv(PROCESSED_DIR / "ball_by_ball.csv", low_memory=False)
    
    bbb_df['Over'] = pd.to_numeric(bbb_df['Over'], errors='coerce').fillna(0)
    
    logging.info("Generating Player Stats...")
    player_stats = PlayerStatsGenerator.generate(matches_df, bbb_df)
    player_stats.to_csv(PROCESSED_DIR / "player_stats.csv", index=False)
    
    logging.info("Generating Venue Stats...")
    venue_stats = VenueStatsGenerator.generate(matches_df, bbb_df)
    venue_stats.to_csv(PROCESSED_DIR / "venue_stats.csv", index=False)
    
    logging.info("Generating Team Stats...")
    team_stats = TeamStatsGenerator.generate(matches_df, bbb_df)
    team_stats.to_csv(PROCESSED_DIR / "team_stats.csv", index=False)
    
    logging.info("Running Validations...")
    report = {
        "Status": "Success",
        "Execution_Time_Seconds": round(time.time() - start_time, 2),
        "Validations": []
    }
    
    report["Validations"].append(validate_dataframe(player_stats, "Player_Stats", "Player_Name"))
    report["Validations"].append(validate_dataframe(venue_stats, "Venue_Stats", "Venue"))
    report["Validations"].append(validate_dataframe(team_stats, "Team_Stats", "Team"))
    
    total_inf = sum([v["Inf_Values"] for v in report["Validations"]])
    total_na = sum([v["Missing_Values"] for v in report["Validations"]])
    
    if total_inf > 0 or total_na > 0:
        logging.warning("Found inf or NA values. Auto-fixing and re-saving...")
        player_stats.replace([np.inf, -np.inf], 0, inplace=True)
        player_stats.fillna(0, inplace=True)
        venue_stats.replace([np.inf, -np.inf], 0, inplace=True)
        venue_stats.fillna(0, inplace=True)
        team_stats.replace([np.inf, -np.inf], 0, inplace=True)
        team_stats.fillna(0, inplace=True)
        
        player_stats.to_csv(PROCESSED_DIR / "player_stats.csv", index=False)
        venue_stats.to_csv(PROCESSED_DIR / "venue_stats.csv", index=False)
        team_stats.to_csv(PROCESSED_DIR / "team_stats.csv", index=False)
        
        report["Validations"] = []
        report["Validations"].append(validate_dataframe(player_stats, "Player_Stats", "Player_Name"))
        report["Validations"].append(validate_dataframe(venue_stats, "Venue_Stats", "Venue"))
        report["Validations"].append(validate_dataframe(team_stats, "Team_Stats", "Team"))
        report["Status"] = "Success (Auto-Fixed)"
        
    with open(PROCESSED_DIR / "analytics_report.json", "w") as f:
        json.dump(report, f, indent=4)
        
    logging.info("Analytics Generation Complete.")
    print(json.dumps(report, indent=4))

if __name__ == "__main__":
    main()
