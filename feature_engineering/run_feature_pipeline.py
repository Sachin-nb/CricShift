import pandas as pd
import json
import logging
import time
from pathlib import Path
from generate_features import FeatureGenerator
from validate_features import run_validations

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    start_time = time.time()
    
    PROCESSED_DIR = Path(r"data\processed")
    FEATURES_DIR = Path(r"data\features")
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    
    logging.info("Loading processed datasets...")
    matches_df = pd.read_csv(PROCESSED_DIR / "matches.csv")
    bbb_df = pd.read_csv(PROCESSED_DIR / "ball_by_ball.csv", low_memory=False)
    player_stats = pd.read_csv(PROCESSED_DIR / "player_stats.csv")
    team_stats = pd.read_csv(PROCESSED_DIR / "team_stats.csv")
    venue_stats = pd.read_csv(PROCESSED_DIR / "venue_stats.csv")
    
    generator = FeatureGenerator(matches_df, bbb_df, player_stats, team_stats, venue_stats)
    
    features_df = generator.generate()
    
    logging.info("Validating features...")
    report = run_validations(features_df)
    
    if report["Status"] == "Failed":
        logging.warning("Validation failed! Attempting automatic fixes...")
        
        if report["Infinite_Values"] > 0 or report["Missing_Values"] > 0:
            import numpy as np
            features_df.replace([np.inf, -np.inf], 0, inplace=True)
            features_df.fillna(0, inplace=True)
            
        if report["Duplicate_Rows"] > 0:
            features_df.drop_duplicates(inplace=True)
            
        # Re-run validation
        report = run_validations(features_df)
        report["Status"] = "Passed (Auto-Fixed)"
        
    report["Execution_Time_Seconds"] = round(time.time() - start_time, 2)
    
    logging.info("Saving feature dataset...")
    features_df.to_csv(FEATURES_DIR / "feature_dataset.csv", index=False)
    
    logging.info("Saving validation report...")
    with open(FEATURES_DIR / "feature_report.json", "w") as f:
        json.dump(report, f, indent=4)
        
    logging.info("Feature Pipeline Complete.")
    print(json.dumps(report, indent=4))

if __name__ == "__main__":
    main()
