import pandas as pd
import numpy as np
import logging

def run_validations(df: pd.DataFrame) -> dict:
    logging.info("Running feature validations...")
    report = {
        "Total_Rows": len(df),
        "Total_Columns": len(df.columns),
        "Missing_Values": int(df.isna().sum().sum()),
        "Duplicate_Rows": int(df.duplicated().sum()),
        "Infinite_Values": 0,
        "Invalid_Labels": 0,
        "Incorrect_DataTypes": 0,
        "Status": "Passed"
    }
    
    # Infinite Values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    infs = np.isinf(df[numeric_cols]).sum().sum()
    report["Infinite_Values"] = int(infs)
    
    # Invalid Labels
    # Labels should be 0 or 1 for Momentum_Shift_Label and Match_Winner_Label
    # Win_Probability_Label should be between 0 and 1
    invalid_momentum = (~df['Momentum_Shift_Label'].isin([0, 1])).sum()
    invalid_winner = (~df['Match_Winner_Label'].isin([0, 1])).sum()
    invalid_prob = ((df['Win_Probability_Label'] < 0) | (df['Win_Probability_Label'] > 1)).sum()
    
    report["Invalid_Labels"] = int(invalid_momentum + invalid_winner + invalid_prob)
    
    # Correct Data Types
    # Check if any column is object when it shouldn't be (except identifiers like Match_ID, Batter, etc.)
    str_cols = ['Match_ID', 'Season', 'Venue', 'Batting_Team', 'Bowling_Team', 'Batter_Name', 'Bowler_Name']
    
    for col in df.columns:
        if col not in str_cols and df[col].dtype == 'object':
            # Innings can be string or numeric, allow it if it is '1' or '2'
            if col == 'Innings':
                continue
            report["Incorrect_DataTypes"] += 1
            logging.warning(f"Column {col} has object dtype but is not a recognized string column.")
            
    if (report["Missing_Values"] > 0 or 
        report["Duplicate_Rows"] > 0 or 
        report["Infinite_Values"] > 0 or 
        report["Invalid_Labels"] > 0 or 
        report["Incorrect_DataTypes"] > 0):
        report["Status"] = "Failed"
        
    return report
