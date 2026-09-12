import pandas as pd
import numpy as np
import logging
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_selection import VarianceThreshold


def create_win_target(df: pd.DataFrame) -> pd.DataFrame:
    """Uses existing Match_Winner_Label as the target.
    
    Match_Winner_Label = 1 if the batting team eventually won the match.
    Match_Winner_Label = 0 otherwise.
    This is independent of prediction features (it's the actual match outcome).
    """
    if 'Match_Winner_Label' not in df.columns:
        raise ValueError("Match_Winner_Label column not found in dataset")
    
    df['Win_Target'] = df['Match_Winner_Label'].astype(int)
    
    dist = df['Win_Target'].value_counts().sort_index()
    logging.info(f"Win target distribution: {dict(dist)}")
    logging.info(f"Win rate: {dist.get(1, 0) / len(df) * 100:.1f}%")
    
    return df


def select_input_features(df: pd.DataFrame) -> list:
    """Returns the list of meaningful input features for win probability prediction."""
    desired_features = [
        'Season', 'Venue', 'Batting_Team', 'Bowling_Team', 'Innings',
        'Current_Over', 'Current_Ball', 'Current_Score', 'Current_Wickets',
        'Balls_Remaining', 'Overs_Remaining', 'Runs_Remaining', 'Target',
        'Current_Run_Rate', 'Required_Run_Rate', 'Required_Run_Rate_Gap',
        'Runs_Last_6_Balls', 'Runs_Last_12_Balls', 'Runs_Last_18_Balls', 'Runs_Last_30_Balls',
        'Wickets_Last_6_Balls', 'Wickets_Last_12_Balls',
        'Boundaries_Last_6_Balls', 'Boundaries_Last_12_Balls',
        'Dot_Balls_Last_6_Balls', 'Dot_Balls_Last_12_Balls',
        'Pressure_Index', 'Boundary_Momentum', 'Dot_Ball_Pressure',
        'Current_Partnership_Runs', 'Current_Partnership_Balls', 'Current_Partnership_Run_Rate',
        'Batter_Career_Average', 'Batter_Career_Strike_Rate',
        'Batter_Boundary_Percentage', 'Batting_Impact_Score',
        'Bowler_Economy', 'Bowler_Strike_Rate', 'Bowler_Dot_Ball_Percentage', 'Bowling_Impact_Score',
        'Team_Win_Percentage', 'Bat_First_Strength', 'Chase_Strength',
        'Venue_Run_Rate', 'Venue_Average_Score', 'Venue_Chasing_Success',
        'Powerplay_Flag', 'Middle_Overs_Flag', 'Death_Overs_Flag', 'Pressure_Overs_Flag'
    ]
    # Only include features that actually exist in the dataframe
    available = [f for f in desired_features if f in df.columns]
    logging.info(f"Selected {len(available)} input features out of {len(desired_features)} desired")
    return available


def preprocess_data(df: pd.DataFrame):
    """Handles missing values and encodes categorical features."""
    encoders = {}
    str_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    for col in str_cols:
        le = LabelEncoder()
        df[col] = df[col].fillna('Missing').astype(str)
        df[col] = le.fit_transform(df[col])
        encoders[col] = le
    
    df = df.fillna(0)
    
    # Replace inf values
    df = df.replace([np.inf, -np.inf], 0)
    
    return df, encoders


def remove_correlated_features(X: pd.DataFrame, correlation_threshold=0.92):
    """Removes highly correlated features and zero-variance features."""
    # Remove zero/near-zero variance
    selector = VarianceThreshold(threshold=0.01)
    selector.fit(X)
    selected_cols = X.columns[selector.get_support()]
    X = X[selected_cols].copy()
    
    # Remove highly correlated
    corr_matrix = X.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = [col for col in upper.columns if any(upper[col] > correlation_threshold)]
    X = X.drop(columns=to_drop)
    
    return X, to_drop
