import os
import json
import logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import time
import pandas as pd

from parser import CricsheetParser
from extract_matches import MatchExtractor
from extract_ball_by_ball import BallByBallExtractor

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

RAW_DIR = Path(r"data\raw\ipl_male_csv")
PROCESSED_DIR = Path(r"data\processed")

def process_file(file_path):
    parser = CricsheetParser(file_path)
    meta, delivs = parser.parse()
    return parser.is_valid, meta, delivs, str(file_path)

def run_etl():
    start_time = time.time()
    
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    all_files = list(RAW_DIR.glob("*.csv"))
    total_files = len(all_files)
    
    summary = {
        "Number of Files": total_files,
        "Matches": 0,
        "Deliveries": 0,
        "Teams": 0,
        "Players": 0,
        "Years": 0,
        "Malformed Files": []
    }
    
    all_meta = []
    all_deliveries = []
    
    logging.info(f"Starting ETL Pipeline. Processing {total_files} files from {RAW_DIR}...")
    
    # Process files in parallel
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {executor.submit(process_file, f): f for f in all_files}
        
        for future in tqdm(as_completed(futures), total=total_files, desc="Parsing CSVs"):
            try:
                is_valid, meta, delivs, file_path = future.result()
                if is_valid:
                    summary["Matches"] += 1
                    all_meta.append(meta)
                    all_deliveries.extend(delivs)
                else:
                    summary["Malformed Files"].append(file_path)
            except Exception as e:
                logging.error(f"Error processing file: {e}")
                
    summary["Deliveries"] = len(all_deliveries)
    
    logging.info("Extracting matches...")
    matches_df = MatchExtractor.extract(all_meta)
    
    logging.info("Extracting ball-by-ball data...")
    bbb_df = BallByBallExtractor.extract(all_deliveries)
    
    # Calculate unique teams, players, years
    teams_set = set(matches_df['Team1'].dropna().unique()).union(set(matches_df['Team2'].dropna().unique()))
    players_set = set(bbb_df['Batter'].dropna().unique()).union(
                  set(bbb_df['Bowler'].dropna().unique()), 
                  set(bbb_df['Non_Striker'].dropna().unique()))
    years_set = set(matches_df['Season'].dropna().unique())
    
    summary["Teams"] = len(teams_set)
    summary["Players"] = len(players_set)
    summary["Years"] = len(years_set)
    
    # Save datasets
    matches_df.to_csv(PROCESSED_DIR / "matches.csv", index=False)
    bbb_df.to_csv(PROCESSED_DIR / "ball_by_ball.csv", index=False)
    
    # Save summary
    with open(PROCESSED_DIR / "dataset_summary.json", "w") as f:
        json.dump(summary, f, indent=4)
        
    end_time = time.time()
    
    print("=" * 50)
    print("ETL PIPELINE COMPLETED")
    print("=" * 50)
    print(f"Total Files Processed: {summary['Number of Files']}")
    print(f"Total Matches:         {summary['Matches']}")
    print(f"Total Deliveries:      {summary['Deliveries']}")
    print(f"Total Teams:           {summary['Teams']}")
    print(f"Total Players:         {summary['Players']}")
    print(f"Total Years:           {summary['Years']}")
    print(f"Processing Time:       {end_time - start_time:.2f} seconds")
    print(f"Validation Errors:     {len(summary['Malformed Files'])}")
    print("=" * 50)

if __name__ == "__main__":
    run_etl()
