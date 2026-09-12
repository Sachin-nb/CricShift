import pickle
import pandas as pd
import numpy as np
from pathlib import Path
import logging


def load_model_assets(model_dir: Path):
    """Loads model, feature columns, and encoders."""
    with open(model_dir / 'best_model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open(model_dir / 'feature_columns.pkl', 'rb') as f:
        feature_cols = pickle.load(f)
    with open(model_dir / 'label_encoder.pkl', 'rb') as f:
        encoders = pickle.load(f)
    return model, feature_cols, encoders


def predict_win_probability(df: pd.DataFrame, model_dir: Path):
    """Predicts win probability for each delivery.
    
    Returns array of probabilities (0-100%) for the batting team winning.
    """
    model, feature_cols, encoders = load_model_assets(model_dir)
    
    df = df.copy()
    str_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    for col in str_cols:
        if col in encoders:
            le = encoders[col]
            df[col] = df[col].fillna('Missing').astype(str)
            df[col] = df[col].map(lambda s: s if s in le.classes_ else le.classes_[0])
            df[col] = le.transform(df[col])
    
    df = df.fillna(0)
    df = df.replace([np.inf, -np.inf], 0)
    
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
    
    X = df[feature_cols]
    probabilities = model.predict_proba(X)[:, 1]
    
    # Convert to percentage
    win_probabilities = (probabilities * 100).round(2)
    
    return win_probabilities
