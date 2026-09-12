import pandas as pd
import numpy as np

def calculate_rolling_features(df: pd.DataFrame, match_col='Match_ID', innings_col='Innings') -> pd.DataFrame:
    """Calculates rolling momentum features within each match innings."""
    
    group_cols = [c for c in [match_col, innings_col] if c in df.columns]
    sort_cols = group_cols + [c for c in ['Over', 'Ball'] if c in df.columns]
    
    # Sort just to be absolutely sure
    if sort_cols:
        df = df.sort_values(sort_cols)
    
    if not group_cols:
        return df  # Cannot group, just return
        
    group = df.groupby(group_cols)
    runs_col = 'Total_Runs' if 'Total_Runs' in df.columns else 'Runs_From_Ball' if 'Runs_From_Ball' in df.columns else None
    
    # Runs
    if runs_col:
        df['Runs_Last_6_Balls'] = group[runs_col].rolling(window=6, min_periods=1).sum().reset_index(level=list(range(len(group_cols))), drop=True)
        df['Runs_Last_12_Balls'] = group[runs_col].rolling(window=12, min_periods=1).sum().reset_index(level=list(range(len(group_cols))), drop=True)
        df['Runs_Last_18_Balls'] = group[runs_col].rolling(window=18, min_periods=1).sum().reset_index(level=list(range(len(group_cols))), drop=True)
        df['Runs_Last_30_Balls'] = group[runs_col].rolling(window=30, min_periods=1).sum().reset_index(level=list(range(len(group_cols))), drop=True)
    
    # Wickets
    if 'Wicket' in df.columns:
        df['Wickets_Last_6_Balls'] = group['Wicket'].rolling(window=6, min_periods=1).sum().reset_index(level=list(range(len(group_cols))), drop=True)
        df['Wickets_Last_12_Balls'] = group['Wicket'].rolling(window=12, min_periods=1).sum().reset_index(level=list(range(len(group_cols))), drop=True)
    
    # Boundaries and Dots
    if 'IsBoundary' in df.columns:
        df['Boundaries_Last_6_Balls'] = group['IsBoundary'].rolling(window=6, min_periods=1).sum().reset_index(level=list(range(len(group_cols))), drop=True)
        df['Boundaries_Last_12_Balls'] = group['IsBoundary'].rolling(window=12, min_periods=1).sum().reset_index(level=list(range(len(group_cols))), drop=True)
    
    if 'IsDotBall' in df.columns:
        df['Dot_Balls_Last_6_Balls'] = group['IsDotBall'].rolling(window=6, min_periods=1).sum().reset_index(level=list(range(len(group_cols))), drop=True)
        df['Dot_Balls_Last_12_Balls'] = group['IsDotBall'].rolling(window=12, min_periods=1).sum().reset_index(level=list(range(len(group_cols))), drop=True)
    
    return df

def calculate_momentum_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates Momentum Score, Boundary Momentum, Dot Ball Pressure, and Pressure Index."""
    
    # Momentum Score = (Runs_Last_12_Balls) - (Wickets_Last_12_Balls * 10)
    df['Momentum_Score'] = df.get('Runs_Last_12_Balls', 0) - (df.get('Wickets_Last_12_Balls', 0) * 10)
    
    # Boundary Momentum = Boundaries_Last_12_Balls * 4
    df['Boundary_Momentum'] = df.get('Boundaries_Last_12_Balls', 0) * 4
    
    # Dot Ball Pressure = Dot_Balls_Last_12_Balls / 12 (as percentage)
    df['Dot_Ball_Pressure'] = (df.get('Dot_Balls_Last_12_Balls', 0) / 12) * 100
    
    # Pressure Index = Required_Run_Rate + (Wickets_Last_6_Balls * 2) + (Dot_Ball_Pressure / 10)
    # Required_Run_Rate must be computed first! We will compute this in main script, so this is a placeholder.
    # We will finalize Pressure_Index in generate_features.py once RRR is available.
    
    return df

def calculate_partnership_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates partnership runs, balls, and run rate."""
    # A partnership is defined by the unique pair of Batter and Non_Striker in a match innings
    # For simplicity, we can just group by Match_ID, Innings, and Wicket count
    
    group_cols = [c for c in ['Match_ID', 'Innings'] if c in df.columns]
    if not group_cols or 'Wicket' not in df.columns:
        return df
        
    df['Partnership_ID'] = df.groupby(group_cols)['Wicket'].cumsum()
    
    group = df.groupby(group_cols + ['Partnership_ID'])
    
    runs_col = 'Total_Runs' if 'Total_Runs' in df.columns else 'Runs_From_Ball' if 'Runs_From_Ball' in df.columns else None
    if runs_col:
        df['Current_Partnership_Runs'] = group[runs_col].cumsum()
        df['Current_Partnership_Balls'] = group.cumcount() + 1
        
        df['Current_Partnership_Run_Rate'] = (df['Current_Partnership_Runs'] / df['Current_Partnership_Balls']) * 6
    
    return df
