import pandas as pd
import numpy as np
import logging
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_selection import VarianceThreshold


def create_momentum_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Creates 3-class momentum shift labels using FUTURE scoring outcomes.
    
    The label answers: "What happens NEXT?" — did scoring accelerate, decelerate,
    or stay neutral in the UPCOMING deliveries compared to the recent past?
    
    This eliminates label leakage because:
    - Features describe the CURRENT game state (past/present).
    - Labels describe what happens NEXT (future outcome).
    - The model cannot reconstruct the label from its inputs.
    
    Logic:
    - Compare runs scored in the NEXT 6 balls vs the PREVIOUS 6 balls.
    - Also factor in wickets falling in the NEXT 6 balls.
    - Positive Momentum (2): Future scoring rate accelerates significantly AND no future wickets.
    - Negative Momentum (0): Future scoring rate decelerates significantly OR multiple future wickets.
    - Neutral Momentum (1): Everything else.
    """
    df = df.sort_values(['Match_ID', 'Innings', 'Current_Over', 'Current_Ball']).copy()
    
    # Calculate future-looking windows (NEXT 6 balls) per innings
    # These are computed purely for label creation and then DROPPED from the dataframe
    grouped = df.groupby(['Match_ID', 'Innings'])
    
    # Runs scored in the NEXT 6 balls (forward-looking rolling sum)
    df['_future_runs_6'] = grouped['Current_Score'].transform(
        lambda x: x.diff().shift(-1).rolling(6, min_periods=1).sum().shift(-5)
    )
    
    # Wickets in the NEXT 6 balls (forward-looking)
    df['_future_wickets_6'] = grouped['Current_Wickets'].transform(
        lambda x: x.diff().shift(-1).rolling(6, min_periods=1).sum().shift(-5)
    )
    
    # Runs scored in the PREVIOUS 6 balls (backward-looking, used only for label)
    df['_past_runs_6'] = grouped['Current_Score'].transform(
        lambda x: x.diff().rolling(6, min_periods=1).sum()
    )
    
    # Fill NaNs (beginning/end of innings)
    df['_future_runs_6'] = df['_future_runs_6'].fillna(df['_past_runs_6'])
    df['_future_wickets_6'] = df['_future_wickets_6'].fillna(0)
    df['_past_runs_6'] = df['_past_runs_6'].fillna(0)
    
    # Calculate scoring rate change
    df['_rr_change'] = df['_future_runs_6'] - df['_past_runs_6']
    
    # Create 3-class labels
    # Negative Momentum (0): Scoring decelerates by >3 runs OR 2+ wickets fall next
    # Positive Momentum (2): Scoring accelerates by >3 runs AND no wickets fall next
    # Neutral Momentum (1): Everything else
    conditions = [
        (df['_rr_change'] < -3) | (df['_future_wickets_6'] >= 2),
        (df['_rr_change'] > 3) & (df['_future_wickets_6'] == 0)
    ]
    choices = [0, 2]
    
    df['Momentum_Class'] = np.select(conditions, choices, default=1)
    
    # Log class distribution
    dist = df['Momentum_Class'].value_counts().sort_index()
    logging.info(f"Label distribution: {dict(dist)}")
    
    # Drop ALL intermediate columns — these must NOT remain in the feature set
    df = df.drop(columns=['_future_runs_6', '_future_wickets_6', '_past_runs_6', '_rr_change'])
    
    return df


def recalculate_partnership(df: pd.DataFrame) -> pd.DataFrame:
    """Recalculates partnership features correctly.
    
    The wicket ball belongs to the OLD partnership.
    The new partnership begins from the NEXT delivery.
    """
    df = df.sort_values(['Match_ID', 'Innings', 'Current_Over', 'Current_Ball']).copy()
    
    # Detect wicket events: where Current_Wickets increases
    df['_ball_wicket'] = df.groupby(['Match_ID', 'Innings'])['Current_Wickets'].diff().fillna(0)
    df['_ball_wicket'] = df['_ball_wicket'].clip(lower=0)
    
    # Runs scored on this ball
    df['_ball_runs'] = df.groupby(['Match_ID', 'Innings'])['Current_Score'].diff().fillna(0)
    df['_ball_runs'] = df['_ball_runs'].clip(lower=0)
    
    # Partnership ID: shift wicket signal forward so wicket ball stays in OLD partnership
    # cumsum of SHIFTED wicket signal means the new partnership starts on the ball AFTER the wicket
    df['_partnership_id'] = df.groupby(['Match_ID', 'Innings'])['_ball_wicket'].transform(
        lambda x: x.shift(1, fill_value=0).cumsum()
    )
    
    # Recalculate partnership stats
    group = df.groupby(['Match_ID', 'Innings', '_partnership_id'])
    df['Current_Partnership_Runs'] = group['_ball_runs'].cumsum()
    df['Current_Partnership_Balls'] = group.cumcount() + 1
    df['Current_Partnership_Run_Rate'] = (
        df['Current_Partnership_Runs'] / df['Current_Partnership_Balls']
    ) * 6
    
    # Replace NaN/inf in run rate
    df['Current_Partnership_Run_Rate'] = df['Current_Partnership_Run_Rate'].replace(
        [np.inf, -np.inf], 0
    ).fillna(0)
    
    # Drop intermediate columns
    df = df.drop(columns=['_ball_wicket', '_ball_runs', '_partnership_id'])
    
    return df


def preprocess_data(df: pd.DataFrame):
    """Handles missing values and categorical features."""
    encoders = {}
    str_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    for col in str_cols:
        le = LabelEncoder()
        df[col] = df[col].fillna('Missing').astype(str)
        df[col] = le.fit_transform(df[col])
        encoders[col] = le
        
    df = df.fillna(0)
    
    if 'Match_ID' in df.columns:
        df = df.drop(columns=['Match_ID'])
        
    return df, encoders


def select_features(X: pd.DataFrame, correlation_threshold=0.90):
    """Removes highly correlated features and zero variance features."""
    selector = VarianceThreshold(threshold=0.01)
    selector.fit(X)
    selected_cols = X.columns[selector.get_support()]
    X = X[selected_cols].copy()
    
    corr_matrix = X.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    to_drop = [column for column in upper.columns if any(upper[column] > correlation_threshold)]
    X = X.drop(columns=to_drop)
    
    return X, to_drop
